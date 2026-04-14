import { useState } from 'react';
import { api } from '../api';

interface Props {
  onLogin: () => void;
  onCancel: () => void;
}

export default function AdminLogin({ onLogin, onCancel }: Props) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim()) {
      setError('请输入管理员账号');
      return;
    }
    if (!password.trim()) {
      setError('请输入管理员密码');
      return;
    }
    setLoading(true);
    setError('');
    try {
      const res = await api.adminLogin(username.trim(), password);
      if (res.success) {
        localStorage.setItem('admin_username', username.trim());
        localStorage.setItem('admin_password', password);
        onLogin();
      } else {
        setError('管理员账号或密码错误');
      }
    } catch {
      setError('管理员账号或密码错误');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-sm mx-4 bg-[var(--color-background)] rounded-2xl border border-[var(--color-border)] p-6 shadow-xl">
        <h2 className="text-lg font-bold text-[var(--color-foreground)] mb-4">
          管理员登录
        </h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            value={username}
            onChange={(e) => {
              setUsername(e.target.value);
              setError('');
            }}
            placeholder="请输入管理员账号"
            className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)] transition-all"
            autoComplete="username"
            autoFocus
          />
          <input
            type="password"
            value={password}
            onChange={(e) => {
              setPassword(e.target.value);
              setError('');
            }}
            placeholder="请输入管理员密码"
            className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-foreground)] focus:outline-none focus:ring-2 focus:ring-[var(--color-foreground)] transition-all"
            autoComplete="current-password"
          />
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 py-2.5 px-4 rounded-xl border border-[var(--color-border)] text-[var(--color-foreground)] hover:bg-[var(--color-border)]/20 transition-all text-sm"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="flex-1 py-2.5 px-4 rounded-xl bg-[var(--color-foreground)] text-[var(--color-background)] font-medium hover:opacity-90 disabled:opacity-50 transition-all text-sm flex items-center justify-center"
            >
              {loading ? '验证中...' : '登录'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
