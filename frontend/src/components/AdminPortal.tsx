import { useEffect, useState } from 'react';
import { ArrowLeft, LockKeyhole, User } from 'lucide-react';
import { api } from '../api';
import { AdminDashboard } from './AdminDashboard';

export default function AdminPortal() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [loggedIn, setLoggedIn] = useState(false);
  const [checkingSavedLogin, setCheckingSavedLogin] = useState(true);

  useEffect(() => {
    const verifySavedLogin = async () => {
      const savedUsername = localStorage.getItem('admin_username');
      const savedPassword = localStorage.getItem('admin_password');
      if (!savedUsername || !savedPassword) {
        setCheckingSavedLogin(false);
        return;
      }

      try {
        await api.getDashboardStats();
        setLoggedIn(true);
      } catch {
        localStorage.removeItem('admin_username');
        localStorage.removeItem('admin_password');
        setLoggedIn(false);
      } finally {
        setCheckingSavedLogin(false);
      }
    };

    verifySavedLogin();
  }, []);

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
      const result = await api.adminLogin(username.trim(), password);
      if (result.success) {
        localStorage.setItem('admin_username', username.trim());
        localStorage.setItem('admin_password', password);
        setLoggedIn(true);
        setUsername('');
        setPassword('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '登录失败');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_username');
    localStorage.removeItem('admin_password');
    setLoggedIn(false);
  };

  if (checkingSavedLogin) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <div className="w-8 h-8 border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (loggedIn) {
    return (
      <div className="min-h-screen bg-[#fafafa] dark:bg-[#050505] text-zinc-900 dark:text-zinc-200">
        <header className="border-b border-zinc-200 dark:border-zinc-800 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-xl">
          <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between gap-4">
            <div>
              <p className="text-sm text-zinc-500 dark:text-zinc-400">独立管理员后台</p>
              <h1 className="text-2xl font-bold tracking-tight">授权码与平台 API 管理</h1>
            </div>
            <div className="flex items-center gap-3">
              <a
                href="/"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-900 transition text-sm"
              >
                <ArrowLeft className="w-4 h-4" />
                返回用户端
              </a>
              <button
                onClick={handleLogout}
                className="px-4 py-2 rounded-xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 text-sm font-medium hover:opacity-90 transition"
              >
                退出后台
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-4 py-8">
          <AdminDashboard />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--color-background)] px-4 py-10 flex items-center justify-center">
      <div className="w-full max-w-5xl grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-950/90 p-8 lg:p-10 shadow-xl">
          <div className="inline-flex items-center gap-4 mb-6">
            <div className="flex items-center justify-center w-14 h-14 rounded-2xl overflow-hidden bg-white shadow-sm ring-1 ring-zinc-200 dark:ring-zinc-800">
              <img src="/aura-logo.png" alt="奥拉·灵感" className="w-full h-full object-cover" />
            </div>
            <div>
              <p className="text-sm font-medium text-zinc-500 dark:text-zinc-400">奥拉·灵感 (Aura Inspiration)</p>
              <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1">独立管理员后台</p>
            </div>
          </div>
          <h1 className="text-3xl lg:text-4xl font-bold tracking-tight text-zinc-950 dark:text-white">
            独立管理员后台
          </h1>
          <p className="mt-4 text-sm lg:text-base leading-7 text-zinc-600 dark:text-zinc-300 max-w-2xl">
            在这里统一完成平台免费 API 配置、授权码生成与禁用管理，普通用户端不再直接暴露这些后台能力。
          </p>
          <div className="mt-8 rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50 dark:bg-zinc-900/60 p-5">
            <div className="text-sm font-semibold text-zinc-900 dark:text-white">本页支持</div>
            <ul className="mt-3 space-y-2 text-sm text-zinc-600 dark:text-zinc-400">
              <li>- 生成、启停、删除授权码</li>
              <li>- 查看用户数、免费用户数、任务总量</li>
              <li>- 配置平台默认云雾 API，供免费用户前 3 次生成使用</li>
            </ul>
          </div>
        </div>

        <div className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-950/95 p-8 shadow-xl">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-zinc-950 dark:text-white">管理员登录</h2>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">输入管理员账号和密码后进入后台。</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">管理员账号</label>
              <div className="relative">
                <User className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  type="text"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    setError('');
                  }}
                  placeholder="请输入管理员账号"
                  className="w-full pl-11 pr-4 py-3 rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                  autoComplete="username"
                  autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">管理员密码</label>
              <div className="relative">
                <LockKeyhole className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setError('');
                  }}
                  placeholder="请输入管理员密码"
                  className="w-full pl-11 pr-4 py-3 rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                  autoComplete="current-password"
                />
              </div>
              {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
            </div>

            <button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              className="w-full py-3 rounded-2xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 font-medium hover:opacity-90 disabled:opacity-50 transition"
            >
              {loading ? '验证中...' : '进入后台'}
            </button>
          </form>

          <a href="/" className="mt-6 inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white transition">
            <ArrowLeft className="w-4 h-4" />
            返回用户首页
          </a>
        </div>
      </div>
    </div>
  );
}
