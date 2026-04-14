import { useState } from 'react';
import { api } from '../api';

interface Props {
  onLogin: (code: string, info: any) => void;
}

export default function LicenseLogin({ onLogin }: Props) {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code.trim()) {
      setError('请输入授权码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.validateLicense(code.trim());
      if (res.valid) {
        localStorage.setItem('license_code', code.trim());
        onLogin(code.trim(), res);
      } else {
        setError('授权码无效');
      }
    } catch (err: any) {
      const detail = err?.detail || err?.message || '授权码验证失败';
      setError(typeof detail === 'string' ? detail : '授权码验证失败');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)] px-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto mb-4 flex items-center justify-center w-16 h-16 rounded-2xl overflow-hidden bg-white shadow-sm ring-1 ring-zinc-200 dark:ring-zinc-800">
            <img src="/aura-logo.png" alt="奥拉·灵感" className="w-full h-full object-cover" />
          </div>
          <h1 className="text-2xl font-bold text-[var(--color-foreground)]">
            奥拉·灵感 (Aura Inspiration)
          </h1>
          <p className="mt-2 text-sm text-[var(--color-muted-foreground)]">
            请输入授权码以使用平台
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <input
              type="text"
              value={code}
              onChange={(e) => {
                setCode(e.target.value.toUpperCase());
                setError('');
              }}
              placeholder="NYAI-XXXX-XXXX-XXXX"
              className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] text-center text-lg font-mono tracking-wider focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)] focus:border-transparent transition-all"
              autoComplete="off"
              autoFocus
            />
            {error && (
              <p className="mt-2 text-sm text-red-500 text-center">{error}</p>
            )}
          </div>

          <button
            type="submit"
            disabled={loading || !code.trim()}
            className="w-full py-3 px-4 rounded-xl bg-[var(--color-foreground)] text-[var(--color-background)] font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                验证中...
              </>
            ) : (
              '激活授权码'
            )}
          </button>
        </form>

        <p className="mt-6 text-xs text-center text-[var(--color-muted)]">
          没有授权码？请联系管理员获取
        </p>
      </div>
    </div>
  );
}
