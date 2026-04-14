import { useEffect, useState } from 'react';
import {
  CheckCircle,
  Copy,
  Image,
  Key,
  Plus,
  Save,
  Settings,
  Shield,
  Trash2,
  Users,
  X,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../api';
import type { AdminDashboardStats, LicenseCode, PlatformApiConfig } from '../types';

const emptyPlatformConfig: PlatformApiConfig = {
  display_name: '云雾平台免费 API',
  base_url: '',
  api_key: '',
  model_name: '',
  api_protocol: 'OpenAI',
  configured: false,
  source: null,
};

export function AdminDashboard() {
  const [stats, setStats] = useState<AdminDashboardStats | null>(null);
  const [codes, setCodes] = useState<LicenseCode[]>([]);
  const [platformConfig, setPlatformConfig] = useState<PlatformApiConfig>(emptyPlatformConfig);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createdCodes, setCreatedCodes] = useState<string[]>([]);
  const [errorMessage, setErrorMessage] = useState('');

  const [createCount, setCreateCount] = useState(1);
  const [createMaxImages, setCreateMaxImages] = useState('');
  const [createExpiresAt, setCreateExpiresAt] = useState('');
  const [createNote, setCreateNote] = useState('');
  const [creating, setCreating] = useState(false);
  const [savingPlatform, setSavingPlatform] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setErrorMessage('');
    try {
      const [statsData, codesData, platformData] = await Promise.all([
        api.getDashboardStats(),
        api.getLicenseCodes(),
        api.getPlatformApiSettings(),
      ]);

      setStats(statsData);
      setCodes(Array.isArray(codesData) ? codesData : []);
      setPlatformConfig(platformData || emptyPlatformConfig);
    } catch (error) {
      console.error('Failed to fetch admin data:', error);
      setErrorMessage(error instanceof Error ? error.message : '后台数据加载失败');
      setStats(null);
      setCodes([]);
      setPlatformConfig(emptyPlatformConfig);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreate = async () => {
    setCreating(true);
    try {
      const res = await api.createLicenseCodes({
        count: createCount,
        max_images: createMaxImages ? Number(createMaxImages) : undefined,
        expires_at: createExpiresAt || undefined,
        note: createNote || undefined,
      });
      setCreatedCodes(res.codes);
      setCreateCount(1);
      setCreateMaxImages('');
      setCreateExpiresAt('');
      setCreateNote('');
      await fetchData();
    } catch (error) {
      alert(error instanceof Error ? error.message : '生成授权码失败');
    } finally {
      setCreating(false);
    }
  };

  const handleToggle = async (code: LicenseCode) => {
    try {
      await api.updateLicenseCode(code.id, { is_active: !code.is_active });
      await fetchData();
    } catch (error) {
      alert(error instanceof Error ? error.message : '更新授权码失败');
    }
  };

  const handleDelete = async (id: string) => {
    if (!window.confirm('确定删除此授权码？')) return;
    try {
      await api.deleteLicenseCode(id);
      await fetchData();
    } catch (error) {
      alert(error instanceof Error ? error.message : '删除授权码失败');
    }
  };

  const handleSavePlatform = async () => {
    if (!platformConfig.base_url.trim() || !platformConfig.api_key.trim() || !platformConfig.model_name.trim()) {
      alert('请先填写完整的平台免费 API 配置');
      return;
    }

    setSavingPlatform(true);
    try {
      const result = await api.updatePlatformApiSettings({
        display_name: platformConfig.display_name,
        base_url: platformConfig.base_url,
        api_key: platformConfig.api_key,
        model_name: platformConfig.model_name,
        api_protocol: platformConfig.api_protocol,
      });
      setPlatformConfig(result);
      alert(result.message || '平台免费 API 配置已保存');
    } catch (error) {
      alert(error instanceof Error ? error.message : '保存平台 API 失败');
    } finally {
      setSavingPlatform(false);
    }
  };

  const copyCode = (code: string) => navigator.clipboard.writeText(code);
  const copyAllCodes = () => navigator.clipboard.writeText(createdCodes.join('\n'));

  if (loading) {
    return <div className="flex items-center justify-center h-96">数据加载中...</div>;
  }

  return (
    <div className="space-y-8">
      {errorMessage && (
        <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600 dark:border-red-900/60 dark:bg-red-950/20 dark:text-red-300">
          {errorMessage}
        </div>
      )}

      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
          <Shield className="w-5 h-5 text-zinc-500" />
          <span>运营大盘</span>
        </h2>
        <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
          {[
            { label: '授权码总数', value: stats?.total_codes || 0, icon: Key, color: 'text-blue-500' },
            { label: '活跃授权码', value: stats?.active_codes || 0, icon: CheckCircle, color: 'text-green-500' },
            { label: '总用户数', value: stats?.total_users || 0, icon: Users, color: 'text-violet-500' },
            { label: '免费用户数', value: stats?.free_users || 0, icon: Users, color: 'text-amber-500' },
            { label: '生成任务数', value: stats?.total_tasks || 0, icon: Image, color: 'text-fuchsia-500' },
            { label: '已生成图片', value: stats?.total_images || 0, icon: Image, color: 'text-orange-500' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className="bg-white dark:bg-zinc-950 p-5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-sm">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-zinc-500 dark:text-zinc-400">{label}</h3>
                <Icon className={cn('w-4 h-4', color)} />
              </div>
              <p className="text-2xl font-bold">{value}</p>
            </div>
          ))}
        </div>
        <div className="mt-3 text-sm text-zinc-500 dark:text-zinc-400">当前任务成功率：{stats?.success_rate || '0%'}</div>
      </div>

      <div className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-950 p-6 shadow-sm space-y-5">
        <div className="flex items-center gap-2">
          <Settings className="w-5 h-5 text-zinc-500" />
          <h2 className="text-xl font-semibold">平台免费 API 配置</h2>
        </div>
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          这套配置会给新注册用户的前 3 次免费生成使用。激活授权码后，用户将改为使用自己的 API 配置。
        </p>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <label className="block text-sm font-medium mb-2">显示名称</label>
            <input
              type="text"
              value={platformConfig.display_name}
              onChange={(e) => setPlatformConfig((prev) => ({ ...prev, display_name: e.target.value }))}
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">模型名称</label>
            <input
              type="text"
              value={platformConfig.model_name}
              onChange={(e) => setPlatformConfig((prev) => ({ ...prev, model_name: e.target.value }))}
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-2">Base URL</label>
            <input
              type="text"
              value={platformConfig.base_url}
              onChange={(e) => setPlatformConfig((prev) => ({ ...prev, base_url: e.target.value }))}
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm font-mono"
            />
          </div>
          <div className="md:col-span-2">
            <label className="block text-sm font-medium mb-2">API Key</label>
            <input
              type="password"
              value={platformConfig.api_key}
              onChange={(e) => setPlatformConfig((prev) => ({ ...prev, api_key: e.target.value }))}
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm font-mono"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">协议</label>
            <select
              value={platformConfig.api_protocol}
              onChange={(e) => setPlatformConfig((prev) => ({ ...prev, api_protocol: e.target.value }))}
              className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm"
            >
              <option value="OpenAI">OpenAI</option>
              <option value="Google API">Google API</option>
            </select>
          </div>
          <div className="flex items-end">
            <div className="text-sm text-zinc-500 dark:text-zinc-400">
              当前状态：{platformConfig.configured ? '已配置' : '未配置'}
              {platformConfig.source ? ` · 来源：${platformConfig.source}` : ''}
            </div>
          </div>
        </div>

        <button
          onClick={handleSavePlatform}
          disabled={savingPlatform}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 disabled:opacity-50 transition"
        >
          <Save className="w-4 h-4" />
          {savingPlatform ? '保存中...' : '保存平台 API'}
        </button>
      </div>

      <div>
        <div className="flex items-center justify-between mb-4 gap-4">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Key className="w-5 h-5 text-zinc-500" />
            <span>授权码管理</span>
          </h2>
          <button
            onClick={() => {
              setShowCreate(true);
              setCreatedCodes([]);
            }}
            className="flex items-center gap-1 bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:hover:bg-zinc-200 text-white dark:text-zinc-900 px-4 py-2 rounded-lg text-sm font-medium transition"
          >
            <Plus className="w-4 h-4" />
            <span>生成授权码</span>
          </button>
        </div>

        {createdCodes.length > 0 && (
          <div className="mb-4 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
            <div className="flex items-center justify-between mb-2 gap-3 flex-wrap">
              <span className="text-sm font-medium text-green-700 dark:text-green-400">已生成 {createdCodes.length} 个授权码</span>
              <div className="flex gap-2">
                <button onClick={copyAllCodes} className="text-xs text-green-600 dark:text-green-400 hover:underline flex items-center gap-1"><Copy className="w-3 h-3" /> 全部复制</button>
                <button onClick={() => setCreatedCodes([])} className="text-xs text-green-600 dark:text-green-400 hover:underline">关闭</button>
              </div>
            </div>
            <div className="font-mono text-sm space-y-1">
              {createdCodes.map((code, index) => (
                <div key={index} className="flex items-center gap-2">
                  <span className="text-green-800 dark:text-green-300">{code}</span>
                  <button onClick={() => copyCode(code)} className="text-green-500 hover:text-green-700"><Copy className="w-3 h-3" /></button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="bg-white dark:bg-zinc-950 rounded-2xl border border-zinc-200 dark:border-zinc-800 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-zinc-100 dark:bg-zinc-900 text-zinc-600 dark:text-zinc-400">
                <tr>
                  <th className="px-6 py-4 font-medium">授权码</th>
                  <th className="px-6 py-4 font-medium">状态</th>
                  <th className="px-6 py-4 font-medium">使用量</th>
                  <th className="px-6 py-4 font-medium">绑定状态</th>
                  <th className="px-6 py-4 font-medium">过期时间</th>
                  <th className="px-6 py-4 font-medium">备注</th>
                  <th className="px-6 py-4 font-medium text-right">操作</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800">
                {codes.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center text-zinc-500">暂无授权码，点击右上角创建</td>
                  </tr>
                ) : (
                  codes.map((code) => (
                    <tr key={code.id} className="hover:bg-zinc-50 dark:hover:bg-zinc-900/50 transition-colors">
                      <td className="px-6 py-4 font-mono text-sm">
                        <div className="flex items-center gap-2">
                          <span>{code.code}</span>
                          <button onClick={() => copyCode(code.code)} className="text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-300"><Copy className="w-3.5 h-3.5" /></button>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <button
                          onClick={() => handleToggle(code)}
                          className={cn(
                            'px-2 py-1 rounded text-xs font-medium transition',
                            code.is_active
                              ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                              : 'bg-zinc-200 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
                          )}
                        >
                          {code.is_active ? '已启用' : '已禁用'}
                        </button>
                      </td>
                      <td className="px-6 py-4">{code.images_used}{code.max_images !== null ? ` / ${code.max_images}` : ' / ∞'} 张</td>
                      <td className="px-6 py-4 text-sm text-zinc-500">{code.owner_user_id ? '已绑定用户' : '未绑定'}</td>
                      <td className="px-6 py-4 text-sm text-zinc-500">{code.expires_at ? new Date(code.expires_at).toLocaleString('zh-CN') : '永不过期'}</td>
                      <td className="px-6 py-4 text-sm text-zinc-500 max-w-40 truncate">{code.note || '-'}</td>
                      <td className="px-6 py-4 text-right">
                        <button onClick={() => handleDelete(code.id)} className="text-zinc-500 hover:text-red-500 transition p-1" title="删除">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {showCreate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
          <div className="bg-white dark:bg-zinc-950 rounded-2xl w-full max-w-md overflow-hidden shadow-2xl border border-zinc-200 dark:border-zinc-800">
            <div className="flex items-center justify-between p-5 border-b border-zinc-200 dark:border-zinc-800">
              <h3 className="text-lg font-semibold">生成授权码</h3>
              <button onClick={() => setShowCreate(false)} className="text-zinc-500 hover:text-zinc-900 dark:hover:text-white"><X className="w-5 h-5" /></button>
            </div>
            <div className="p-5 space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">生成数量</label>
                <input type="number" min={1} max={50} value={createCount} onChange={(e) => setCreateCount(Number(e.target.value) || 1)} className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">最大图片数（留空 = 无限）</label>
                <input type="number" min={1} value={createMaxImages} onChange={(e) => setCreateMaxImages(e.target.value)} className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">过期时间（留空 = 永不过期）</label>
                <input type="datetime-local" value={createExpiresAt} onChange={(e) => setCreateExpiresAt(e.target.value)} className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">备注（可选）</label>
                <input type="text" value={createNote} onChange={(e) => setCreateNote(e.target.value)} placeholder="例如：外部客户 / 内部测试" className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-zinc-50 dark:bg-zinc-950 px-4 py-2.5 text-sm" />
              </div>
            </div>
            <div className="p-5 border-t border-zinc-200 dark:border-zinc-800 flex justify-end gap-3">
              <button onClick={() => setShowCreate(false)} className="px-5 py-2.5 rounded-xl text-sm font-medium border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition">取消</button>
              <button onClick={handleCreate} disabled={creating} className="px-5 py-2.5 rounded-xl text-sm font-medium bg-zinc-900 dark:bg-white text-white dark:text-zinc-900 hover:opacity-90 disabled:opacity-50 transition">{creating ? '生成中...' : '生成'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
