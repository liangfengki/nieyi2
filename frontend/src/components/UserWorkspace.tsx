import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box,
  CheckSquare,
  Download,
  History,
  Image as ImageIcon,
  KeyRound,
  LogOut,
  Mail,
  Moon,
  Settings,
  Sparkles,
  Square,
  Sun,
  Trash2,
  Upload,
  User,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../api';
import UserApiConfig from './UserApiConfig';
import type {
  PlanResult,
  SessionResponse,
  ShotSelection,
  StrategiesResponse,
  UserAPIConfig,
} from '../types';

interface Props {
  session: SessionResponse;
  onSessionChange: (payload: SessionResponse) => void;
  onLogout: () => void;
}

const compressImage = async (blob: Blob, maxWidth = 1920, maxHeight = 1920, quality = 0.85): Promise<Blob> => {
  return new Promise((resolve) => {
    const img = new Image();
    img.src = URL.createObjectURL(blob);
    img.onload = () => {
      let width = img.width;
      let height = img.height;
      if (width > maxWidth || height > maxHeight) {
        const ratio = Math.min(maxWidth / width, maxHeight / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
      }
      const canvas = document.createElement('canvas');
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) {
        resolve(blob);
        return;
      }
      ctx.drawImage(img, 0, 0, width, height);
      canvas.toBlob((compressedBlob) => resolve(compressedBlob || blob), 'image/jpeg', quality);
    };
    img.onerror = () => resolve(blob);
  });
};

export default function UserWorkspace({ session, onSessionChange, onLogout }: Props) {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [currentView, setCurrentView] = useState<'workspace' | 'history'>('workspace');
  const [showApiConfig, setShowApiConfig] = useState(false);

  const [mannequinImages, setMannequinImages] = useState<string[]>([]);
  const [modelImage, setModelImage] = useState<string | null>(null);
  const [product3dImage, setProduct3dImage] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedImages, setGeneratedImages] = useState<string[]>([]);
  const [planResults, setPlanResults] = useState<PlanResult[]>([]);
  const [historyImages, setHistoryImages] = useState<string[]>([]);
  const [historyPlanResults, setHistoryPlanResults] = useState<PlanResult[]>([]);
  const [modelMode, setModelMode] = useState<'ai_generate' | 'reference_model'>('ai_generate');
  const [customPrompt, setCustomPrompt] = useState('');
  const [selectedModelId, setSelectedModelId] = useState('');
  const [availableModels, setAvailableModels] = useState<UserAPIConfig[]>([]);
  const [strategies, setStrategies] = useState<StrategiesResponse | null>(null);
  const [selectedPersonaId, setSelectedPersonaId] = useState('european_natural');
  const [selectedShotCounts, setSelectedShotCounts] = useState<Map<string, number>>(new Map());
  const [selectedTextLevel, setSelectedTextLevel] = useState('no_text');
  const [selectedBustType, setSelectedBustType] = useState('full_round');
  const [selectedSkinTone, setSelectedSkinTone] = useState('light');
  const [selectedImages, setSelectedImages] = useState<Set<number>>(new Set());
  const [previewImage, setPreviewImage] = useState<string | null>(null);
  const [isDraggingMannequin, setIsDraggingMannequin] = useState(false);
  const [isDraggingModel, setIsDraggingModel] = useState(false);
  const [progressText, setProgressText] = useState('');
  const [activationCode, setActivationCode] = useState('');
  const [activationLoading, setActivationLoading] = useState(false);
  const [activationError, setActivationError] = useState('');
  const [loadingData, setLoadingData] = useState(true);
  const [showLicensePanel, setShowLicensePanel] = useState(false);

  const totalSelected = useMemo(
    () => Array.from(selectedShotCounts.values()).reduce((sum, count) => sum + count, 0),
    [selectedShotCounts],
  );

  const hasFreeQuota = session.user.free_remaining > 0;
  const isReferenceModelMode = modelMode === 'reference_model';

  const refreshSession = useCallback(async () => {
    try {
      const payload = await api.getSessionMe();
      onSessionChange(payload);
    } catch (error) {
      console.error('Failed to refresh session:', error);
    }
  }, [onSessionChange]);

  const syncHistory = useCallback((history: { tasks: Array<{ status: string; images?: string[]; plan_results?: unknown[] }> }) => {
    const allImages: string[] = [];
    const allPlanResults: PlanResult[] = [];

    for (const task of history.tasks) {
      if (task.status !== 'completed' || !task.images) continue;
      for (let i = 0; i < task.images.length; i += 1) {
        allImages.push(api.getImageUrl(task.images[i]));
        const result = task.plan_results?.[i];
        if (result && typeof result === 'object') {
          allPlanResults.push(result as PlanResult);
        } else {
          allPlanResults.push({ shot_type: '', shot_name: '', image_url: '' });
        }
      }
    }

    setHistoryImages(allImages);
    setHistoryPlanResults(allPlanResults);
  }, []);

  const loadUserData = useCallback(async () => {
    setLoadingData(true);
    try {
      const [strategiesData, historyData] = await Promise.all([
        api.getStrategies(),
        api.getHistory(),
      ] as const);
      setStrategies(strategiesData);
      syncHistory(historyData);

      if (session.user.has_active_license) {
        const configs = await api.getUserApiConfigs().catch(() => []);
        const activeGenerationModels = configs.filter((item) => item.is_active && item.purpose === 'generation');
        const nextModels = activeGenerationModels.length > 0 ? activeGenerationModels : configs.filter((item) => item.is_active);
        setAvailableModels(nextModels);
        setSelectedModelId(nextModels[0]?.id || '');
      } else {
        setAvailableModels([]);
        setSelectedModelId('');
      }
    } catch (error) {
      console.error('Failed to load workspace data:', error);
      alert(`加载数据失败：${error instanceof Error ? error.message : '请稍后重试'}`);
    } finally {
      setLoadingData(false);
    }
  }, [session.user.has_active_license, syncHistory]);

  useEffect(() => {
    loadUserData();
  }, [loadUserData]);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDarkMode]);

  const toggleShotType = (shotTypeId: string) => {
    setSelectedShotCounts((prev) => {
      const next = new Map(prev);
      const currentCount = next.get(shotTypeId) || 0;
      if (currentCount > 0) {
        next.delete(shotTypeId);
      } else {
        next.set(shotTypeId, 1);
      }
      return next;
    });
  };

  const selectAllShotTypes = () => {
    if (!strategies) return;
    const counts = new Map<string, number>();
    Object.keys(strategies.shot_types).forEach((key) => counts.set(key, 1));
    setSelectedShotCounts(counts);
  };

  const deselectAllShotTypes = () => setSelectedShotCounts(new Map());

  const processMannequinFiles = (files: File[]) => {
    const imageFiles = files.filter((file) => file.type.startsWith('image/'));
    if (imageFiles.length === 0) return;
    const urls = imageFiles.map((file) => URL.createObjectURL(file));
    setMannequinImages((prev) => [...prev, ...urls]);
  };

  const processModelFile = (file: File) => {
    if (file && file.type.startsWith('image/')) {
      setModelImage(URL.createObjectURL(file));
    }
  };

  const handleImageUpload = (
    event: React.ChangeEvent<HTMLInputElement>,
    setImage: React.Dispatch<React.SetStateAction<string | null>>,
  ) => {
    const file = event.target.files?.[0];
    if (file) {
      setImage(URL.createObjectURL(file));
    }
  };

  const handleMultipleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    processMannequinFiles(files);
  };

  const removeMannequinImage = (indexToRemove: number) => {
    setMannequinImages((prev) => prev.filter((_, index) => index !== indexToRemove));
  };

  const handleOpenApiConfig = () => {
    if (!session.user.has_active_license) {
      alert('请先激活授权码，激活后才能配置您自己的 API。');
      return;
    }
    setShowApiConfig(true);
  };

  const handleModelModeChange = (nextMode: 'ai_generate' | 'reference_model') => {
    setModelMode(nextMode);

    if (nextMode === 'reference_model' && !modelImage) {
      window.setTimeout(() => {
        document.getElementById('reference-model-upload')?.scrollIntoView({
          behavior: 'smooth',
          block: 'center',
        });
      }, 80);
      alert('已切换到“参考模特图”模式，请先上传参考模特图。');
    }
  };

  const handleActivateLicense = async () => {
    if (!activationCode.trim()) {
      setActivationError('请输入授权码');
      return;
    }

    setActivationLoading(true);
    setActivationError('');
    try {
      const payload = await api.activateLicense(activationCode.trim().toUpperCase());
      onSessionChange(payload);
      setActivationCode('');
      setShowLicensePanel(false);
      await loadUserData();
    } catch (error) {
      setActivationError(error instanceof Error ? error.message : '激活失败');
    } finally {
      setActivationLoading(false);
    }
  };

  const handleGenerate = async () => {
    if (mannequinImages.length === 0) {
      alert('请至少上传一张商品图 / 人台图');
      return;
    }
    if (totalSelected === 0) {
      alert('请至少选择一个拍摄类型');
      return;
    }
    if (selectedShotCounts.has('pose_reference') && (selectedShotCounts.get('pose_reference') || 0) > 0 && !modelImage) {
      alert('您选择了“跟随参考姿势”，请先上传参考模特图。');
      return;
    }
    if (session.user.has_active_license && availableModels.length === 0) {
      alert('请先配置并启用您自己的 API Key。');
      return;
    }
    if (!session.user.has_active_license && !hasFreeQuota) {
      alert('免费次数已用完，请先激活授权码继续使用。');
      return;
    }

    setIsGenerating(true);
    setSelectedImages(new Set());
    setProgressText('正在提交任务...');

    try {
      const formData = new FormData();
      formData.append('persona_id', selectedPersonaId);
      formData.append('text_level', selectedTextLevel);
      formData.append('bust_type', selectedBustType);
      formData.append('skin_tone', selectedSkinTone);
      formData.append('model_mode', modelMode);

      const plans: ShotSelection[] = [];
      selectedShotCounts.forEach((count, shotType) => {
        for (let i = 0; i < count; i += 1) {
          plans.push({ shot_type: shotType });
        }
      });
      formData.append('selected_plans', JSON.stringify(plans));

      if (customPrompt.trim()) {
        formData.append('custom_prompt', customPrompt.trim());
      }
      if (session.user.has_active_license && selectedModelId) {
        formData.append('model_id', selectedModelId);
      }

      for (let i = 0; i < mannequinImages.length; i += 1) {
        const blob = await fetch(mannequinImages[i]).then((res) => res.blob());
        const compressedBlob = await compressImage(blob);
        const file = new File([compressedBlob], `mannequin_${i}.jpg`, { type: 'image/jpeg' });
        formData.append('mannequin_images', file);
      }

      if (modelImage) {
        const blob = await fetch(modelImage).then((res) => res.blob());
        const compressedBlob = await compressImage(blob);
        const file = new File([compressedBlob], 'model.jpg', { type: 'image/jpeg' });
        formData.append('model_image', file);
      }

      if (product3dImage) {
        const blob = await fetch(product3dImage).then((res) => res.blob());
        const compressedBlob = await compressImage(blob);
        const file = new File([compressedBlob], 'product_3d.jpg', { type: 'image/jpeg' });
        formData.append('product_3d_image', file);
      }

      const taskData = await api.generate(formData);
      const taskId = taskData.task_id;
      setProgressText(taskData.message || `任务已提交，正在生成 ${totalSelected} 张图片...`);

      const pollInterval = window.setInterval(async () => {
        try {
          const statusData = await api.getTask(taskId);

          if (statusData.status === 'completed') {
            window.clearInterval(pollInterval);
            const imageUrls = (statusData.images || []).map((url) => api.getImageUrl(url));
            const newPlanResults = (statusData.plan_results || []) as PlanResult[];
            setGeneratedImages(imageUrls);
            setPlanResults(newPlanResults);
            setHistoryImages((prev) => [...imageUrls, ...prev]);
            setHistoryPlanResults((prev) => [...newPlanResults, ...prev]);
            setIsGenerating(false);
            setProgressText('');
            refreshSession();
          } else if (statusData.status === 'failed') {
            window.clearInterval(pollInterval);
            setIsGenerating(false);
            setProgressText('');
            refreshSession();
            alert(`生成失败：${statusData.error_message || '请稍后重试'}`);
          } else if (statusData.product_dna) {
            setProgressText('DNA 已提取，正在生成图片...');
          }
        } catch (error) {
          console.error('Error polling task status:', error);
        }
      }, 2000);
    } catch (error) {
      console.error('Error generating images:', error);
      setIsGenerating(false);
      setProgressText('');
      alert(`提交任务失败：${error instanceof Error ? error.message : '请检查后端服务是否正常'}`);
      refreshSession();
    }
  };

  const toggleImageSelection = (index: number, event: React.MouseEvent) => {
    event.stopPropagation();
    const next = new Set(selectedImages);
    if (next.has(index)) {
      next.delete(index);
    } else {
      next.add(index);
    }
    setSelectedImages(next);
  };

  const toggleSelectAll = () => {
    if (selectedImages.size === historyImages.length) {
      setSelectedImages(new Set());
    } else {
      setSelectedImages(new Set(historyImages.map((_, index) => index)));
    }
  };

  const handleBatchDelete = () => {
    if (selectedImages.size === 0) {
      alert('请先选择要删除的图片');
      return;
    }
    if (!window.confirm(`确定要删除选中的 ${selectedImages.size} 张图片吗？`)) return;
    setHistoryImages((prev) => prev.filter((_, index) => !selectedImages.has(index)));
    setHistoryPlanResults((prev) => prev.filter((_, index) => !selectedImages.has(index)));
    setSelectedImages(new Set());
  };

  const downloadImage = (url: string, filename: string) => {
    const anchor = document.createElement('a');
    if (url.startsWith('data:')) {
      anchor.href = url;
      anchor.download = `${filename}.jpg`;
    } else {
      try {
        const urlObj = new URL(url, window.location.origin);
        const path = urlObj.pathname;
        const ext = path.split('.').pop() || 'jpg';
        anchor.href = url.startsWith('http') ? url : api.getDownloadUrl(path);
        anchor.download = `${filename}.${ext}`;
      } catch {
        anchor.href = url;
        anchor.download = `${filename}.jpg`;
      }
    }
    anchor.style.display = 'none';
    document.body.appendChild(anchor);
    anchor.click();
    setTimeout(() => anchor.remove(), 100);
  };

  const handleBatchDownload = () => {
    if (historyImages.length === 0) return;
    const indices = selectedImages.size > 0 ? Array.from(selectedImages) : historyImages.map((_, index) => index);
    indices.forEach((index) => downloadImage(historyImages[index], `generated_model_${index + 1}`));
  };

  const shotTypeIcon = (icon: string) => {
    const icons: Record<string, React.ReactNode> = {
      user: <User className="w-4 h-4" />,
      box: <Box className="w-4 h-4" />,
    };
    return icons[icon] || <Sparkles className="w-4 h-4" />;
  };

  const selectionSummary = session.user.has_active_license
    ? `本次预计消耗 ${totalSelected} 张授权额度`
    : `本次将消耗 1 次免费生成机会`;

  const quotaBadge = session.user.has_active_license
    ? `授权码剩余 ${session.license?.remaining ?? '∞'} 张`
    : `免费剩余 ${session.user.free_remaining} 次`;

  const generateDisabled = isGenerating
    || mannequinImages.length === 0
    || totalSelected === 0
    || (session.user.has_active_license && availableModels.length === 0)
    || (!session.user.has_active_license && !hasFreeQuota);

  const generateButtonLabel = isGenerating
    ? (progressText || 'AI 正在生成...')
    : `开始生成（${totalSelected} 张）`;

  const generateHelperText = isGenerating
    ? '任务已提交，正在后台处理中'
    : mannequinImages.length === 0
      ? '先上传商品图 / 人台图'
      : totalSelected === 0
        ? '至少选择一个拍摄类型'
        : isReferenceModelMode && !modelImage
          ? '参考模特图模式下，必须先上传参考模特图'
          : session.user.has_active_license && availableModels.length === 0
            ? '先配置并启用您自己的 API'
            : !session.user.has_active_license && !hasFreeQuota
              ? '免费次数已用完，请先激活授权码'
              : selectionSummary;

  const shellWidthClass = 'w-full max-w-[1680px]';

  if (loadingData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <div className="w-8 h-8 border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#fafafa] dark:bg-[#050505] text-zinc-900 dark:text-zinc-200 transition-colors duration-200 flex flex-col">
      <header className="border-b border-zinc-200/80 dark:border-zinc-800 bg-white/70 dark:bg-zinc-950/80 backdrop-blur-xl">
        <div className={cn(shellWidthClass, 'mx-auto px-4 py-4 flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between')}>
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-10 h-10 rounded-2xl overflow-hidden bg-white shadow-sm ring-1 ring-zinc-200 dark:ring-zinc-800 flex items-center justify-center">
              <img src="/aura-logo.png" alt="奥拉·灵感" className="w-full h-full object-cover" />
            </div>
            <div className="min-w-0">
              <div className="font-semibold truncate text-zinc-950 dark:text-white">奥拉·灵感 (Aura Inspiration)</div>
              <div className="text-xs text-zinc-500 dark:text-zinc-400 flex items-center gap-1 truncate mt-0.5">
                <Mail className="w-3 h-3" />
                {session.user.email}
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-3 xl:items-end">
            <div className="inline-flex w-fit items-center rounded-2xl bg-zinc-100 dark:bg-zinc-900 p-1 shadow-sm">
              <button
                onClick={() => setCurrentView('workspace')}
                className={cn(
                  'inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition',
                  currentView === 'workspace'
                    ? 'bg-white dark:bg-zinc-800 text-zinc-950 dark:text-white shadow-sm font-semibold'
                    : 'text-zinc-500 dark:text-zinc-400',
                )}
              >
                <Sparkles className="w-4 h-4" />
                工作台
              </button>
              <button
                onClick={() => setCurrentView('history')}
                className={cn(
                  'inline-flex items-center gap-2 rounded-xl px-4 py-2 text-sm transition',
                  currentView === 'history'
                    ? 'bg-white dark:bg-zinc-800 text-zinc-950 dark:text-white shadow-sm font-semibold'
                    : 'text-zinc-500 dark:text-zinc-400',
                )}
              >
                <History className="w-4 h-4" />
                生成记录
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-2 xl:justify-end">
              <span className="inline-flex items-center rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-3 py-2 text-xs text-zinc-600 dark:text-zinc-300">
                {quotaBadge}
              </span>
              <button
                onClick={handleOpenApiConfig}
                className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
              >
                <KeyRound className="w-4 h-4" />
                API 配置
              </button>
              <button
                onClick={() => setIsDarkMode((prev) => !prev)}
                className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
              >
                {isDarkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                {isDarkMode ? '浅色' : '深色'}
              </button>
              <button
                onClick={onLogout}
                className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-3 py-2 text-sm text-zinc-700 dark:text-zinc-200 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
              >
                <LogOut className="w-4 h-4" />
                退出
              </button>
            </div>
          </div>
        </div>
      </header>

      <main className={cn(shellWidthClass, 'mx-auto flex-1 space-y-6 px-4 py-6 pb-32 md:pb-36')}>
        <section className={cn(
          'rounded-3xl border p-5 md:p-6 shadow-sm',
          session.user.has_active_license
            ? 'border-emerald-200 bg-emerald-50 dark:border-emerald-900/60 dark:bg-emerald-950/20'
            : session.user.free_remaining > 0
              ? 'border-blue-200 bg-blue-50 dark:border-blue-900/60 dark:bg-blue-950/20'
              : 'border-amber-200 bg-amber-50 dark:border-amber-900/60 dark:bg-amber-950/20',
        )}>
          {session.user.has_active_license ? (
            <>
              <div className="flex flex-col gap-4 xl:flex-row xl:items-center xl:justify-between">
                <div className="min-w-0 flex-1">
                  <div className="inline-flex items-center rounded-full bg-emerald-100 dark:bg-emerald-900/40 px-3 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-300">
                    授权码模式已开启
                  </div>
                  <div className="mt-3 flex flex-wrap items-stretch gap-3">
                    <div className="min-w-[260px] rounded-2xl border border-white/70 dark:border-zinc-800 bg-white/90 dark:bg-zinc-950/70 px-4 py-3 shadow-sm">
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">当前授权码</div>
                      <div className="mt-1 font-mono text-lg font-semibold text-zinc-950 dark:text-white truncate">
                        {session.license?.code ?? '--'}
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/70 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-4 py-3 shadow-sm">
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">授权额度</div>
                      <div className="mt-1 text-sm font-semibold text-zinc-900 dark:text-white">
                        剩余 {session.license?.remaining ?? '∞'} 张
                      </div>
                    </div>
                    <div className="rounded-2xl border border-white/70 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 px-4 py-3 shadow-sm">
                      <div className="text-xs text-zinc-500 dark:text-zinc-400">账号状态</div>
                      <div className="mt-1 text-sm font-semibold text-zinc-900 dark:text-white">
                        已切换到自有 API
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <button
                    onClick={handleOpenApiConfig}
                    className="inline-flex items-center gap-2 rounded-xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 px-4 py-2.5 text-sm font-medium hover:opacity-90 transition"
                  >
                    <KeyRound className="w-4 h-4" />
                    API 配置
                  </button>
                  <button
                    onClick={() => setShowLicensePanel((prev) => !prev)}
                    className="inline-flex items-center gap-2 rounded-xl border border-emerald-200 dark:border-emerald-800 bg-white/80 dark:bg-zinc-950/60 px-4 py-2.5 text-sm text-zinc-700 dark:text-zinc-200 hover:border-emerald-300 dark:hover:border-emerald-700 transition"
                  >
                    {showLicensePanel ? '收起授权码面板' : '查看授权码面板'}
                  </button>
                </div>
              </div>

              {showLicensePanel && (
                <div className="mt-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_auto] rounded-2xl border border-white/70 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/60 p-4 shadow-sm">
                  <div>
                    <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-white mb-3">
                      <Settings className="w-4 h-4" />
                      授权码面板
                    </div>
                    <p className="text-sm leading-6 text-zinc-600 dark:text-zinc-300">
                      当前账号已绑定授权码，后续生成会直接使用您自己的 API。若要核对授权码信息或重新输入，可在这里操作。
                    </p>
                  </div>
                  <div className="w-full lg:w-[420px]">
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={activationCode}
                        onChange={(e) => {
                          setActivationCode(e.target.value.toUpperCase());
                          setActivationError('');
                        }}
                        placeholder={session.license?.code ?? 'NYAI-XXXX-XXXX-XXXX'}
                        className="flex-1 px-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                      />
                      <button
                        onClick={handleActivateLicense}
                        disabled={activationLoading || !activationCode.trim()}
                        className="px-4 py-2.5 rounded-xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
                      >
                        {activationLoading ? '激活中...' : '确认'}
                      </button>
                    </div>
                    {activationError && <p className="mt-2 text-sm text-red-500">{activationError}</p>}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex flex-col gap-5 xl:flex-row xl:items-center xl:justify-between">
              <div className="space-y-3 flex-1">
                <div className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
                  {hasFreeQuota ? '当前为免费体验账号' : '免费次数已用完，待激活授权码'}
                </div>
                <h2 className="text-2xl font-bold tracking-tight text-zinc-950 dark:text-white">
                  {hasFreeQuota ? `还可免费生成 ${session.user.free_remaining} 次` : '请激活授权码继续使用'}
                </h2>
                <p className="text-sm leading-6 text-zinc-600 dark:text-zinc-300 max-w-3xl">
                  免费体验期间由平台默认云雾 API 代为出图；一旦激活授权码，后续将切换为您自己的 API。
                </p>
                <div className="flex flex-wrap gap-2 text-sm text-zinc-600 dark:text-zinc-300">
                  <span className="inline-flex items-center rounded-full bg-white/80 dark:bg-zinc-950/60 px-3 py-1.5 border border-white/70 dark:border-zinc-800">
                    免费已使用 {session.user.free_generations_used} / {session.user.free_generations_limit}
                  </span>
                  <span className="inline-flex items-center rounded-full bg-white/80 dark:bg-zinc-950/60 px-3 py-1.5 border border-white/70 dark:border-zinc-800">
                    激活后切换到自有 API
                  </span>
                </div>
              </div>

              <div className="w-full xl:max-w-lg rounded-2xl border border-white/60 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/70 p-4 shadow-sm">
                <div className="flex items-center gap-2 text-sm font-semibold text-zinc-900 dark:text-white mb-3">
                  <Settings className="w-4 h-4" />
                  激活授权码
                </div>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={activationCode}
                    onChange={(e) => {
                      setActivationCode(e.target.value.toUpperCase());
                      setActivationError('');
                    }}
                    placeholder="NYAI-XXXX-XXXX-XXXX"
                    className="flex-1 px-4 py-2.5 rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                  />
                  <button
                    onClick={handleActivateLicense}
                    disabled={activationLoading || !activationCode.trim()}
                    className="px-4 py-2.5 rounded-xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
                  >
                    {activationLoading ? '激活中...' : '激活'}
                  </button>
                </div>
                {activationError && <p className="mt-2 text-sm text-red-500">{activationError}</p>}
                <div className="mt-3 text-xs text-zinc-500 dark:text-zinc-400 leading-5">
                  激活成功后，点击顶部 <span className="font-medium">API 配置</span> 填写您自己的中转地址、Key 和模型名。
                </div>
              </div>
            </div>
          )}
        </section>

        {currentView === 'workspace' && (
          <div className="grid gap-6 2xl:grid-cols-[minmax(0,1.16fr)_minmax(540px,0.96fr)]">
            <aside className="grid gap-5 2xl:grid-cols-[minmax(300px,0.88fr)_minmax(360px,1.12fr)] 2xl:items-start">
              <div className="space-y-5">
                <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm">
                  <div className="mb-3 flex items-center justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold flex items-center gap-2"><ImageIcon className="w-4 h-4" /> 商品图 / 人台图</h3>
                      <p className="mt-1 text-xs text-zinc-500">大屏会自动铺开展示，减少上传区的纵向占用。</p>
                    </div>
                    <span className="text-xs text-zinc-500 whitespace-nowrap">{mannequinImages.length} 张</span>
                  </div>
                  <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 xl:grid-cols-2 3xl:grid-cols-3">
                    {mannequinImages.map((url, index) => (
                      <div key={index} className="relative group rounded-2xl overflow-hidden aspect-square border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900">
                        <img src={url} alt={`mannequin-${index}`} className="w-full h-full object-cover" />
                        <button
                          onClick={() => removeMannequinImage(index)}
                          className="absolute top-2 right-2 rounded-full px-2 py-1 text-xs bg-black/60 text-white opacity-0 group-hover:opacity-100 transition"
                        >
                          删除
                        </button>
                      </div>
                    ))}
                    <div
                      className={cn(
                        'relative border-2 border-dashed rounded-2xl aspect-square flex flex-col items-center justify-center text-center cursor-pointer transition',
                        isDraggingMannequin
                          ? 'border-zinc-900 dark:border-white bg-zinc-100 dark:bg-zinc-900'
                          : 'border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900/60',
                      )}
                      onDragOver={(e) => {
                        e.preventDefault();
                        setIsDraggingMannequin(true);
                      }}
                      onDragLeave={(e) => {
                        e.preventDefault();
                        setIsDraggingMannequin(false);
                      }}
                      onDrop={(e) => {
                        e.preventDefault();
                        setIsDraggingMannequin(false);
                        processMannequinFiles(Array.from(e.dataTransfer.files));
                      }}
                    >
                      <input type="file" accept="image/*" multiple className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleMultipleImageUpload} />
                      <Upload className="w-5 h-5 text-zinc-400" />
                      <span className="mt-2 text-xs text-zinc-500">点击或拖拽上传</span>
                    </div>
                  </div>
                </section>

                <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm space-y-4">
                  <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-1">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold">参考模特图</h3>
                        {modelImage && <button onClick={() => setModelImage(null)} className="text-xs text-zinc-500 hover:text-red-500">删除</button>}
                      </div>
                      <div
                        className={cn(
                          'relative border-2 border-dashed rounded-2xl min-h-28 flex items-center justify-center text-center cursor-pointer overflow-hidden transition',
                          isDraggingModel
                            ? 'border-zinc-900 dark:border-white bg-zinc-100 dark:bg-zinc-900'
                            : 'border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900/60',
                        )}
                        onDragOver={(e) => {
                          e.preventDefault();
                          setIsDraggingModel(true);
                        }}
                        onDragLeave={(e) => {
                          e.preventDefault();
                          setIsDraggingModel(false);
                        }}
                        onDrop={(e) => {
                          e.preventDefault();
                          setIsDraggingModel(false);
                          const file = e.dataTransfer.files?.[0];
                          if (file) processModelFile(file);
                        }}
                      >
                        <input type="file" accept="image/*" className="absolute inset-0 opacity-0 cursor-pointer" onChange={(e) => handleImageUpload(e, setModelImage)} />
                        {modelImage ? (
                          <img src={modelImage} alt="model" className="max-h-56 w-full object-contain" />
                        ) : (
                          <div className="text-sm text-zinc-500">点击或拖拽上传参考模特图</div>
                        )}
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-semibold flex items-center gap-2"><Box className="w-4 h-4" /> 3D 产品图</h3>
                        {product3dImage && <button onClick={() => setProduct3dImage(null)} className="text-xs text-zinc-500 hover:text-red-500">删除</button>}
                      </div>
                      <div className="relative border-2 border-dashed border-zinc-300 dark:border-zinc-700 rounded-2xl min-h-28 flex items-center justify-center text-center cursor-pointer overflow-hidden hover:bg-zinc-50 dark:hover:bg-zinc-900/60 transition">
                        <input
                          type="file"
                          accept="image/*"
                          className="absolute inset-0 opacity-0 cursor-pointer"
                          onChange={(e) => {
                            const file = e.target.files?.[0];
                            if (!file) return;
                            const reader = new FileReader();
                            reader.onload = (event) => setProduct3dImage(event.target?.result as string);
                            reader.readAsDataURL(file);
                          }}
                        />
                        {product3dImage ? (
                          <img src={product3dImage} alt="product-3d" className="max-h-56 w-full object-contain" />
                        ) : (
                          <div className="text-sm text-zinc-500">点击上传 3D 产品参考图</div>
                        )}
                      </div>
                    </div>
                  </div>
                </section>
              </div>

              <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">生成参数</h3>
                    <p className="mt-1 text-xs text-zinc-500">参数区会优先横向展开，宽屏下无需一直下滑。</p>
                  </div>
                  <span className="text-xs text-zinc-500">{selectionSummary}</span>
                </div>

                <div className="space-y-2">
                  <label className="block text-xs text-zinc-500">模型来源</label>
                  {session.user.has_active_license ? (
                    availableModels.length > 0 ? (
                      <select
                        value={selectedModelId}
                        onChange={(e) => setSelectedModelId(e.target.value)}
                        className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2.5 text-sm"
                      >
                        {availableModels.map((model) => (
                          <option key={model.id} value={model.id}>{model.display_name} ({model.model_name})</option>
                        ))}
                      </select>
                    ) : (
                      <button onClick={handleOpenApiConfig} className="w-full rounded-xl border-2 border-dashed border-zinc-300 dark:border-zinc-700 py-3 text-sm text-zinc-500 hover:text-zinc-950 dark:hover:text-white transition">
                        去配置我的 API
                      </button>
                    )
                  ) : (
                    <div className="rounded-xl border border-blue-200 dark:border-blue-900/60 bg-blue-50 dark:bg-blue-950/30 px-4 py-3 text-sm text-blue-700 dark:text-blue-300">
                      当前使用平台免费云雾 API
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <label className="block text-xs text-zinc-500">模特模式</label>
                  <div className="grid grid-cols-2 gap-2">
                    {[
                      { id: 'ai_generate', label: 'AI 自由生成' },
                      { id: 'reference_model', label: '参考模特图' },
                    ].map((item) => (
                      <button
                        key={item.id}
                        onClick={() => handleModelModeChange(item.id as 'ai_generate' | 'reference_model')}
                        className={cn(
                          'rounded-xl border px-3 py-2.5 text-sm transition',
                          modelMode === item.id
                            ? 'border-zinc-900 dark:border-white bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                            : 'border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400',
                          item.id === 'reference_model' && isReferenceModelMode && !modelImage
                            ? 'ring-1 ring-amber-400 border-amber-400 dark:border-amber-500'
                            : '',
                        )}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                  {isReferenceModelMode && (
                    <div className="rounded-2xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs leading-5 text-amber-700 dark:border-amber-900/60 dark:bg-amber-950/20 dark:text-amber-300">
                      该模式会直接读取参考模特图的外观特征，因此下方“模特风格”将不可选择；若尚未上传参考图，系统会要求你先上传。
                    </div>
                  )}
                </div>

                {strategies && (
                  <>
                    <div className="grid gap-4 xl:grid-cols-2 2xl:grid-cols-1">
                      <div className="space-y-2">
                        <div className="flex items-center justify-between gap-3">
                          <label className="block text-xs text-zinc-500">模特风格</label>
                          {isReferenceModelMode && <span className="text-[11px] text-amber-600 dark:text-amber-400">参考模特图模式下不可选</span>}
                        </div>
                        <select
                          value={selectedPersonaId}
                          onChange={(e) => setSelectedPersonaId(e.target.value)}
                          disabled={isReferenceModelMode}
                          className={cn(
                            'w-full rounded-xl border px-3 py-2.5 text-sm transition',
                            isReferenceModelMode
                              ? 'border-zinc-200 dark:border-zinc-800 bg-zinc-100 dark:bg-zinc-900 text-zinc-400 dark:text-zinc-500 cursor-not-allowed'
                              : 'border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white',
                          )}
                        >
                          {Object.entries(strategies.personas).map(([id, persona]) => (
                            <option key={id} value={id}>{persona.name} - {persona.description}</option>
                          ))}
                        </select>
                      </div>

                      <div className="space-y-2">
                        <label className="block text-xs text-zinc-500">图片文字</label>
                        <div className="space-y-2">
                          {Object.entries(strategies.text_levels).map(([id, item]) => (
                            <label key={id} className={cn('flex items-start gap-3 rounded-xl border px-3 py-3 cursor-pointer transition', selectedTextLevel === id ? 'border-zinc-900 dark:border-white bg-zinc-50 dark:bg-zinc-900/70' : 'border-zinc-200 dark:border-zinc-800')}>
                              <input type="radio" checked={selectedTextLevel === id} onChange={() => setSelectedTextLevel(id)} />
                              <div>
                                <div className="text-sm font-medium">{item.name}</div>
                                <div className="text-xs text-zinc-500">{item.description}</div>
                              </div>
                            </label>
                          ))}
                        </div>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-xs text-zinc-500">胸型</label>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(strategies.bust_types).map(([id, item]) => (
                          <button
                            key={id}
                            onClick={() => setSelectedBustType(id)}
                            className={cn(
                              'rounded-xl border px-3 py-2 text-xs transition',
                              selectedBustType === id
                                ? 'border-zinc-900 dark:border-white bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                                : 'border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400',
                            )}
                            title={item.description}
                          >
                            {item.name}
                          </button>
                        ))}
                      </div>
                    </div>

                    <div className="space-y-2">
                      <label className="block text-xs text-zinc-500">肤色</label>
                      <div className="flex flex-wrap gap-2">
                        {Object.entries(strategies.skin_tones).map(([id, item]) => (
                          <button
                            key={id}
                            onClick={() => setSelectedSkinTone(id)}
                            className={cn(
                              'rounded-xl border px-3 py-2 text-xs transition',
                              selectedSkinTone === id
                                ? 'border-zinc-900 dark:border-white bg-zinc-900 dark:bg-white text-white dark:text-zinc-900'
                                : 'border-zinc-300 dark:border-zinc-700 text-zinc-600 dark:text-zinc-400',
                            )}
                            title={item.description}
                          >
                            {item.name}
                          </button>
                        ))}
                      </div>
                    </div>
                  </>
                )}

                <div className="space-y-2">
                  <label className="block text-xs text-zinc-500">附加提示词</label>
                  <textarea
                    value={customPrompt}
                    onChange={(e) => setCustomPrompt(e.target.value)}
                    placeholder="例如：加入更强的棚拍打光、提升高级感..."
                    className="w-full rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-3 min-h-24 text-sm"
                  />
                </div>
              </section>

              <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-5 shadow-sm space-y-4 2xl:col-span-2">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="text-sm font-semibold">选择拍摄类型</h3>
                    <p className="mt-1 text-xs text-zinc-500">宽屏下拍摄方案会自动横向排布，减少滚动距离。</p>
                  </div>
                  <div className="flex items-center gap-2 text-xs">
                    <button
                      onClick={selectAllShotTypes}
                      className="rounded-full border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-3 py-1.5 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
                    >
                      全选
                    </button>
                    <button
                      onClick={deselectAllShotTypes}
                      className="rounded-full border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/50 px-3 py-1.5 text-zinc-600 dark:text-zinc-300 hover:border-zinc-300 dark:hover:border-zinc-700 transition"
                    >
                      清空
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {strategies ? Object.entries(strategies.shot_types).map(([id, shot]) => {
                    const count = selectedShotCounts.get(id) || 0;
                    return (
                      <div key={id} className={cn('rounded-2xl border p-3 transition', count > 0 ? 'border-zinc-900 dark:border-white bg-zinc-50 dark:bg-zinc-900/70' : 'border-zinc-200 dark:border-zinc-800')}>
                        <button onClick={() => toggleShotType(id)} className="w-full text-left">
                          <div className="flex items-center justify-between gap-2">
                            <div className="flex items-center gap-2 text-sm font-medium">
                              {shotTypeIcon(shot.icon)}
                              <span>{shot.name}</span>
                            </div>
                            <span className="text-xs text-zinc-500">{count > 0 ? `${count} 张` : '未选'}</span>
                          </div>
                          <p className="mt-2 text-xs text-zinc-500 leading-5">{shot.description}</p>
                        </button>
                        {count > 0 && (
                          <div className="mt-3 flex items-center justify-between gap-3">
                            <button
                              onClick={() => setSelectedShotCounts((prev) => {
                                const next = new Map(prev);
                                if (count <= 1) next.delete(id); else next.set(id, count - 1);
                                return next;
                              })}
                              className="w-8 h-8 rounded-full border border-zinc-300 dark:border-zinc-700"
                            >
                              -
                            </button>
                            <span className="text-sm font-semibold">{count}</span>
                            <button
                              onClick={() => setSelectedShotCounts((prev) => {
                                const next = new Map(prev);
                                if (count < 10) next.set(id, count + 1);
                                return next;
                              })}
                              className="w-8 h-8 rounded-full border border-zinc-300 dark:border-zinc-700"
                            >
                              +
                            </button>
                          </div>
                        )}
                      </div>
                    );
                  }) : <div className="text-sm text-zinc-500">拍摄策略加载中...</div>}
                </div>

                <div className="rounded-2xl border border-dashed border-zinc-300 dark:border-zinc-700 bg-zinc-50/80 dark:bg-zinc-900/40 px-4 py-3">
                  <div className="text-sm font-medium text-zinc-900 dark:text-white">生成入口已固定到底部</div>
                  <p className="mt-1 text-xs leading-5 text-zinc-500 dark:text-zinc-400">
                    现在无论你滚动到哪里，都可以直接使用底部悬浮操作栏提交任务，不用再回到底部找按钮。
                  </p>
                </div>
              </section>
            </aside>

            <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm min-h-[640px] 2xl:sticky 2xl:top-6 2xl:max-h-[calc(100vh-9.5rem)] flex flex-col overflow-hidden">
              <div className="flex items-center justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-lg font-semibold flex items-center gap-2"><Sparkles className="w-5 h-5 text-zinc-500" /> 生成结果</h2>
                  <p className="text-sm text-zinc-500 mt-1">平台会自动提取产品 DNA 并按方案并发生图。</p>
                </div>
                <button
                  onClick={handleBatchDownload}
                  disabled={generatedImages.length === 0}
                  className="text-sm text-zinc-500 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-white disabled:opacity-50 transition inline-flex items-center gap-2"
                >
                  <Download className="w-4 h-4" /> 批量下载
                </button>
              </div>

              <div className="flex-1 rounded-3xl bg-zinc-50 dark:bg-zinc-900/40 border border-zinc-200 dark:border-zinc-800 p-4 relative overflow-auto min-h-[420px]">
                {isGenerating ? (
                  <div className="absolute inset-0 flex items-center justify-center p-6">
                    <div className="text-center space-y-4">
                      <div className="w-16 h-16 mx-auto border-4 border-zinc-200 dark:border-zinc-700 border-t-zinc-900 dark:border-t-white rounded-full animate-spin" />
                      <div>
                        <div className="font-medium">{progressText || '正在执行工作流...'}</div>
                        <div className="text-sm text-zinc-500 mt-2">提取 DNA → 组装提示词 → 调用模型 → 回传结果</div>
                      </div>
                    </div>
                  </div>
                ) : generatedImages.length > 0 ? (
                  <div className="grid grid-cols-2 gap-4 xl:grid-cols-3 2xl:grid-cols-2">
                    {generatedImages.map((src, index) => (
                      <div key={src + index} onClick={() => setPreviewImage(src)} className="relative group rounded-2xl overflow-hidden border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 cursor-zoom-in">
                        <div onClick={(e) => toggleImageSelection(index, e)} className="absolute top-3 left-3 z-10 text-white drop-shadow-md cursor-pointer">
                          {selectedImages.has(index) ? <CheckSquare className="w-5 h-5 fill-zinc-900 dark:fill-white" /> : <Square className="w-5 h-5 opacity-0 group-hover:opacity-100 transition" />}
                        </div>
                        {planResults[index] && (
                          <div className="absolute top-3 right-3 z-10 rounded-full bg-black/65 text-white text-[10px] px-2 py-1">
                            {planResults[index].shot_name}
                          </div>
                        )}
                        <img src={src} alt={`generated-${index}`} className="w-full aspect-[3/4] object-cover" />
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            downloadImage(src, `generated_model_${index + 1}`);
                          }}
                          className="absolute inset-x-4 bottom-4 py-2 rounded-xl bg-white/92 text-zinc-900 text-sm font-medium opacity-0 group-hover:opacity-100 transition"
                        >
                          下载图片
                        </button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="h-full flex flex-col items-center justify-center text-center text-zinc-400 dark:text-zinc-600 gap-3">
                    <ImageIcon className="w-14 h-14 opacity-30" />
                    <div className="text-lg font-medium">结果将在这里出现</div>
                    <p className="text-sm max-w-md">上传图片、选择拍摄方案后即可开始生成。免费模式下会消耗 1 次试用次数，授权码模式下会消耗对应图片额度。</p>
                  </div>
                )}
              </div>
            </section>
          </div>
        )}

        {currentView === 'history' && (
          <section className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm min-h-[720px] flex flex-col">
            <div className="flex items-center justify-between gap-4 mb-6">
              <div className="flex items-center gap-4">
                <h2 className="text-lg font-semibold flex items-center gap-2"><History className="w-5 h-5 text-zinc-500" /> 生成记录</h2>
                {historyImages.length > 0 && (
                  <button onClick={toggleSelectAll} className="text-sm text-zinc-500 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-white inline-flex items-center gap-2 transition">
                    {selectedImages.size === historyImages.length ? <CheckSquare className="w-4 h-4" /> : <Square className="w-4 h-4" />}
                    {selectedImages.size === historyImages.length ? '取消全选' : '全选'}
                  </button>
                )}
              </div>

              <div className="flex items-center gap-3">
                {selectedImages.size > 0 && (
                  <button onClick={handleBatchDelete} className="text-sm text-red-500 hover:text-red-600 inline-flex items-center gap-2 transition">
                    <Trash2 className="w-4 h-4" /> 删除已选 ({selectedImages.size})
                  </button>
                )}
                <button onClick={handleBatchDownload} disabled={historyImages.length === 0} className="text-sm text-zinc-500 hover:text-zinc-950 dark:text-zinc-400 dark:hover:text-white disabled:opacity-50 inline-flex items-center gap-2 transition">
                  <Download className="w-4 h-4" /> {selectedImages.size > 0 ? `下载已选 (${selectedImages.size})` : '批量下载全部'}
                </button>
              </div>
            </div>

            {historyImages.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                {historyImages.map((src, index) => (
                  <div key={src + index} onClick={() => setPreviewImage(src)} className={cn('relative group rounded-2xl overflow-hidden border cursor-zoom-in transition', selectedImages.has(index) ? 'border-zinc-900 dark:border-white' : 'border-zinc-200 dark:border-zinc-800')}>
                    <div onClick={(e) => toggleImageSelection(index, e)} className="absolute top-3 left-3 z-10 text-white drop-shadow-md cursor-pointer">
                      {selectedImages.has(index) ? <CheckSquare className="w-5 h-5 fill-zinc-900 dark:fill-white" /> : <Square className="w-5 h-5 opacity-0 group-hover:opacity-100 transition" />}
                    </div>
                    {historyPlanResults[index] && historyPlanResults[index].shot_name && (
                      <div className="absolute top-3 right-3 z-10 rounded-full bg-black/65 text-white text-[10px] px-2 py-1">
                        {historyPlanResults[index].shot_name}
                      </div>
                    )}
                    <img src={src} alt={`history-${index}`} className="w-full aspect-[3/4] object-cover" />
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        downloadImage(src, `history_model_${index + 1}`);
                      }}
                      className="absolute inset-x-4 bottom-4 py-2 rounded-xl bg-white/92 text-zinc-900 text-sm font-medium opacity-0 group-hover:opacity-100 transition"
                    >
                      下载图片
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <div className="flex-1 flex flex-col items-center justify-center text-zinc-500 gap-3">
                <History className="w-14 h-14 opacity-30" />
                <div className="text-lg font-medium">暂无生成记录</div>
                <p className="text-sm">生成完成后的图片会自动出现在这里。</p>
              </div>
            )}
          </section>
        )}
      </main>

      {currentView === 'workspace' && (
        <div className="fixed inset-x-0 bottom-0 z-40 px-3 pb-3 pt-4">
          <div className={cn(shellWidthClass, 'mx-auto rounded-[28px] border border-zinc-200/80 dark:border-zinc-800 bg-white/92 dark:bg-zinc-950/92 shadow-[0_-12px_40px_rgba(0,0,0,0.08)] backdrop-blur-xl')}>
            <div className="flex flex-col gap-3 px-4 py-4 md:flex-row md:items-center md:justify-between md:px-5">
              <div className="min-w-0">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center rounded-full bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 px-3 py-1 text-xs font-semibold">
                    已选 {totalSelected} 张
                  </span>
                  <span className="inline-flex items-center rounded-full bg-zinc-100 dark:bg-zinc-900 px-3 py-1 text-xs text-zinc-600 dark:text-zinc-300">
                    商品图 {mannequinImages.length} 张
                  </span>
                  <span className="inline-flex items-center rounded-full bg-zinc-100 dark:bg-zinc-900 px-3 py-1 text-xs text-zinc-600 dark:text-zinc-300">
                    {quotaBadge}
                  </span>
                </div>
                <div className="mt-2 text-sm font-medium text-zinc-900 dark:text-white truncate">
                  {generateHelperText}
                </div>
                <p className="mt-1 text-xs text-zinc-500 dark:text-zinc-400">
                  生成按钮已固定，浏览参数和结果时也能直接提交。
                </p>
              </div>

              <div className="flex items-center gap-3 md:flex-shrink-0">
                <button
                  onClick={handleGenerate}
                  disabled={generateDisabled}
                  className={cn(
                    'flex-1 md:flex-none min-w-[220px] py-3.5 px-5 rounded-2xl font-medium flex items-center justify-center gap-2 transition shadow-sm',
                    generateDisabled
                      ? 'bg-zinc-200 dark:bg-zinc-800 text-zinc-400 cursor-not-allowed'
                      : 'bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90',
                  )}
                >
                  {isGenerating ? <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" /> : <Sparkles className="w-4 h-4" />}
                  <span>{generateButtonLabel}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {previewImage && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/90 backdrop-blur-md p-4" onClick={() => setPreviewImage(null)}>
          <img src={previewImage} alt="preview" className="max-w-full max-h-[90vh] object-contain rounded-2xl shadow-2xl" onClick={(e) => e.stopPropagation()} />
        </div>
      )}

      {showApiConfig && (
        <UserApiConfig
          onClose={() => {
            setShowApiConfig(false);
            loadUserData();
            refreshSession();
          }}
        />
      )}
    </div>
  );
}
