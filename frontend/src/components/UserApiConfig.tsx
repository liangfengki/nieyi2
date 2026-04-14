import { useState, useEffect } from 'react';
import { api } from '../api';
import type { ProviderPreset, UserAPIConfig } from '../types';

interface Props {
  onClose: () => void;
}

export default function UserApiConfig({ onClose }: Props) {
  const [configs, setConfigs] = useState<UserAPIConfig[]>([]);
  const [presets, setPresets] = useState<ProviderPreset[]>([]);
  const [loading, setLoading] = useState(true);

  // Add form state
  const [showAdd, setShowAdd] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<ProviderPreset | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [modelName, setModelName] = useState('');
  const [baseUrl, setBaseUrl] = useState('');
  const [apiProtocol, setApiProtocol] = useState('OpenAI');
  const [displayName, setDisplayName] = useState('');
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [cfgs, prs] = await Promise.all([
        api.getUserApiConfigs(),
        api.getProviderPresets(),
      ]);
      setConfigs(cfgs);
      setPresets(prs);
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePresetSelect = (preset: ProviderPreset) => {
    setSelectedPreset(preset);
    setModelName(preset.default_model);
    setBaseUrl(preset.base_url);
    setApiProtocol(preset.api_protocol);
    setDisplayName(preset.name);
    setTestResult(null);
  };

  const handleTest = async () => {
    if (!apiKey.trim() || !baseUrl.trim()) return;
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testUserConnection({
        base_url: baseUrl,
        api_key: apiKey,
        model_name: modelName,
        api_protocol: apiProtocol,
      });
      setTestResult(res);
    } catch {
      setTestResult({ success: false, message: '测试请求失败' });
    } finally {
      setTesting(false);
    }
  };

  const handleSave = async () => {
    if (!apiKey.trim() || !modelName.trim() || !baseUrl.trim()) return;
    setSaving(true);
    try {
      await api.createUserApiConfig({
        provider_preset_id: selectedPreset?.id || 'custom',
        display_name: displayName || modelName,
        model_name: modelName,
        api_key: apiKey,
        base_url: baseUrl,
        api_protocol: apiProtocol,
        purpose: 'generation',
      });
      setShowAdd(false);
      resetForm();
      await loadData();
    } catch (err) {
      console.error('Failed to save:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此配置？')) return;
    try {
      await api.deleteUserApiConfig(id);
      await loadData();
    } catch (err) {
      console.error('Failed to delete:', err);
    }
  };

  const handleToggle = async (config: UserAPIConfig) => {
    try {
      await api.updateUserApiConfig(config.id, { is_active: !config.is_active });
      await loadData();
    } catch (err) {
      console.error('Failed to toggle:', err);
    }
  };

  const resetForm = () => {
    setSelectedPreset(null);
    setApiKey('');
    setModelName('');
    setBaseUrl('');
    setApiProtocol('OpenAI');
    setDisplayName('');
    setTestResult(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 backdrop-blur-sm">
      <div className="w-full max-w-2xl mx-4 max-h-[85vh] rounded-2xl border border-[var(--color-border)] bg-white/96 dark:bg-[var(--color-background)]/96 shadow-2xl flex flex-col overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-[var(--color-border)] bg-white/90 dark:bg-[var(--color-background)]/90">
          <h2 className="text-lg font-bold text-[var(--color-foreground)]">
            API 配置
          </h2>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-[var(--color-border)]/30 transition-colors">
            <svg className="w-5 h-5 text-[var(--color-muted-foreground)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 bg-zinc-50/70 dark:bg-transparent">
          {loading ? (
            <div className="text-center py-8 text-[var(--color-muted-foreground)]">加载中...</div>
          ) : (
            <>
              {/* Existing configs */}
              {configs.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-sm font-medium text-[var(--color-muted-foreground)]">已配置的 API</h3>
                  {configs.map((c) => (
                    <div key={c.id} className="flex items-center gap-3 p-3 rounded-xl border border-[var(--color-border)] bg-white dark:bg-zinc-950/80 shadow-sm">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="font-medium text-sm text-[var(--color-foreground)]">{c.display_name}</span>
                          <span className="text-xs px-1.5 py-0.5 rounded bg-zinc-100 dark:bg-zinc-900 text-[var(--color-muted-foreground)]">{c.model_name}</span>
                        </div>
                        <div className="text-xs text-[var(--color-muted-foreground)] mt-0.5 font-mono">{c.api_key}</div>
                      </div>
                      <button
                        onClick={() => handleToggle(c)}
                        className={`shrink-0 text-xs px-2.5 py-1 rounded-lg transition-colors ${
                          c.is_active
                            ? 'bg-green-500/10 text-green-700 dark:text-green-400 hover:bg-green-500/20'
                            : 'bg-zinc-100 dark:bg-zinc-900 text-[var(--color-muted-foreground)] hover:bg-zinc-200 dark:hover:bg-zinc-800'
                        }`}
                      >
                        {c.is_active ? '已启用' : '已禁用'}
                      </button>
                      <button
                        onClick={() => handleDelete(c.id)}
                        className="shrink-0 p-1.5 rounded-lg hover:bg-red-500/10 text-[var(--color-muted-foreground)] hover:text-red-500 transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  ))}
                </div>
              )}

              {/* Add button */}
              {!showAdd && (
                <button
                  onClick={() => setShowAdd(true)}
                  className="w-full py-3 px-4 rounded-xl border-2 border-dashed border-[var(--color-border)] text-[var(--color-muted-foreground)] bg-white dark:bg-zinc-950/70 hover:border-[var(--color-foreground)] hover:text-[var(--color-foreground)] transition-all text-sm"
                >
                  + 添加 API 配置
                </button>
              )}

              {/* Add form */}
              {showAdd && (
                <div className="space-y-4 p-4 rounded-xl border border-[var(--color-border)] bg-white dark:bg-zinc-950/70 shadow-sm">
                  <h3 className="text-sm font-medium text-[var(--color-foreground)]">选择 API 中转站</h3>

                  {/* Preset grid */}
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                    {presets.filter(p => p.id !== 'custom').map((p) => (
                      <button
                        key={p.id}
                        onClick={() => handlePresetSelect(p)}
                        className={`p-2.5 rounded-xl border bg-white dark:bg-zinc-950 text-left transition-all text-xs ${
                          selectedPreset?.id === p.id
                            ? 'border-[var(--color-foreground)] bg-zinc-100 dark:bg-zinc-900 shadow-sm'
                            : 'border-[var(--color-border)] hover:border-[var(--color-foreground)]/50 hover:bg-zinc-50 dark:hover:bg-zinc-900/80'
                        }`}
                      >
                        <div className="font-medium text-[var(--color-foreground)] truncate">{p.name}</div>
                        <div className="text-[var(--color-muted-foreground)] mt-0.5 truncate">{p.description}</div>
                      </button>
                    ))}
                    <button
                      onClick={() => handlePresetSelect(presets.find(p => p.id === 'custom')!)}
                      className={`p-2.5 rounded-xl border bg-white dark:bg-zinc-950 text-left transition-all text-xs ${
                        selectedPreset?.id === 'custom'
                          ? 'border-[var(--color-foreground)] bg-zinc-100 dark:bg-zinc-900 shadow-sm'
                          : 'border-[var(--color-border)] hover:border-[var(--color-foreground)]/50 hover:bg-zinc-50 dark:hover:bg-zinc-900/80'
                      }`}
                    >
                      <div className="font-medium text-[var(--color-foreground)]">自定义</div>
                      <div className="text-[var(--color-muted-foreground)] mt-0.5">自定义 API 端点</div>
                    </button>
                  </div>

                  {/* Form fields */}
                  {selectedPreset && (
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-[var(--color-muted-foreground)] mb-1">显示名称</label>
                        <input
                          type="text"
                          value={displayName}
                          onChange={(e) => setDisplayName(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)]"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--color-muted-foreground)] mb-1">API Key *</label>
                        <input
                          type="password"
                          value={apiKey}
                          onChange={(e) => setApiKey(e.target.value)}
                          placeholder="sk-xxxxxxxxxxxx"
                          className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)]"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--color-muted-foreground)] mb-1">模型名称</label>
                        <input
                          type="text"
                          value={modelName}
                          onChange={(e) => setModelName(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] text-sm focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)]"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--color-muted-foreground)] mb-1">Base URL</label>
                        <input
                          type="text"
                          value={baseUrl}
                          onChange={(e) => setBaseUrl(e.target.value)}
                          className="w-full px-3 py-2 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] text-sm font-mono focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)]"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-[var(--color-muted-foreground)] mb-1">API 协议</label>
                        <div className="flex gap-2">
                          {['OpenAI', 'Google API'].map((p) => (
                            <button
                              key={p}
                              onClick={() => setApiProtocol(p)}
                              className={`flex-1 py-2 rounded-lg border text-sm transition-all ${
                                apiProtocol === p
                                  ? 'border-[var(--color-foreground)] bg-[var(--color-foreground)] text-[var(--color-background)]'
                                  : 'border-[var(--color-border)] text-[var(--color-foreground)] bg-white dark:bg-zinc-950 hover:bg-zinc-50 dark:hover:bg-zinc-900/80'
                              }`}
                            >
                              {p}
                            </button>
                          ))}
                        </div>
                      </div>

                      {/* Test & Save */}
                      <div className="flex gap-2 pt-2">
                        <button
                          onClick={handleTest}
                          disabled={testing || !apiKey.trim() || !baseUrl.trim()}
                          className="flex-1 py-2.5 rounded-xl border border-[var(--color-border)] bg-white dark:bg-zinc-950 text-[var(--color-foreground)] text-sm hover:bg-zinc-50 dark:hover:bg-zinc-900/80 disabled:opacity-50 transition-all"
                        >
                          {testing ? '测试中...' : '测试连接'}
                        </button>
                        <button
                          onClick={handleSave}
                          disabled={saving || !apiKey.trim() || !modelName.trim()}
                          className="flex-1 py-2.5 rounded-xl bg-[var(--color-foreground)] text-[var(--color-background)] text-sm font-medium hover:opacity-90 disabled:opacity-50 transition-all"
                        >
                          {saving ? '保存中...' : '保存配置'}
                        </button>
                      </div>

                      {testResult && (
                        <div className={`p-3 rounded-lg text-sm ${
                          testResult.success ? 'bg-green-500/10 text-green-700 dark:text-green-400' : 'bg-red-500/10 text-red-600 dark:text-red-400'
                        }`}>
                          {testResult.success ? '✓ ' : '✗ '}{testResult.message}
                        </div>
                      )}

                      <button
                        onClick={() => { setShowAdd(false); resetForm(); }}
                        className="w-full py-2 text-sm text-[var(--color-muted-foreground)] hover:text-[var(--color-foreground)] transition-colors"
                      >
                        取消
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
