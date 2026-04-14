import { useEffect, useState } from 'react';
import { ArrowLeft, Mail, ShieldCheck, Sparkles } from 'lucide-react';
import { api } from '../api';
import type { SessionResponse } from '../types';

interface Props {
  onLogin: (payload: SessionResponse) => void;
}

type LoginStep = 'email' | 'code';

export default function EmailLogin({ onLogin }: Props) {
  const [step, setStep] = useState<LoginStep>('email');
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [cooldown, setCooldown] = useState(0);
  const [expiresIn, setExpiresIn] = useState(0);
  const [debugCode, setDebugCode] = useState('');

  useEffect(() => {
    if (cooldown <= 0) {
      return;
    }

    const timer = window.setTimeout(() => {
      setCooldown((value) => Math.max(0, value - 1));
    }, 1000);

    return () => window.clearTimeout(timer);
  }, [cooldown]);

  const requestCode = async () => {
    const normalizedEmail = email.trim();
    if (!normalizedEmail) {
      setError('请输入邮箱');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const response = await api.requestEmailCode(normalizedEmail);
      setStep('code');
      setNotice(response.message);
      setCooldown(response.resend_in_seconds);
      setExpiresIn(response.expires_in_seconds);
      setDebugCode(response.debug_code ?? '');
    } catch (err) {
      const message = err instanceof Error ? err.message : '验证码发送失败，请稍后重试';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    await requestCode();
  };

  const handleVerifyCode = async (e: React.FormEvent) => {
    e.preventDefault();
    const normalizedCode = code.trim();
    if (!normalizedCode) {
      setError('请输入验证码');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const payload = await api.verifyEmailCode(email.trim(), normalizedCode);
      onLogin(payload);
    } catch (err) {
      const message = err instanceof Error ? err.message : '登录失败，请稍后重试';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep('email');
    setCode('');
    setError('');
    setNotice('');
    setDebugCode('');
    setCooldown(0);
  };

  const expiryMinutes = Math.max(1, Math.ceil(expiresIn / 60));

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
              <p className="text-xs text-zinc-400 dark:text-zinc-500 mt-1">内衣视觉灵感与生图工作台</p>
            </div>
          </div>
          <div className="space-y-4">
            <div>
              <h1 className="mt-2 text-3xl lg:text-4xl font-bold tracking-tight text-zinc-950 dark:text-white">
                先用邮箱验证码登录，再进入工作台
              </h1>
            </div>
            <p className="text-sm lg:text-base leading-7 text-zinc-600 dark:text-zinc-300 max-w-2xl">
              现在改为真实邮箱验证码校验，不再按 IP 复用账号。每个邮箱都是独立账号，授权码也会绑定到对应账号上。
            </p>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {[
              {
                icon: Mail,
                title: '验证码确认身份',
                desc: '先发送 6 位验证码，确认邮箱归属后再登录。',
              },
              {
                icon: Sparkles,
                title: '免费体验 3 次',
                desc: '新账号默认可免费生成 3 次，用完再激活授权码。',
              },
              {
                icon: ShieldCheck,
                title: '授权码绑定账号',
                desc: '授权码跟随已验证的邮箱账号，不会再因同 IP 自动串号。',
              },
            ].map(({ icon: Icon, title, desc }) => (
              <div key={title} className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-zinc-50/80 dark:bg-zinc-900/60 p-4">
                <Icon className="w-5 h-5 text-zinc-500 mb-3" />
                <div className="text-sm font-semibold text-zinc-900 dark:text-white">{title}</div>
                <p className="mt-1 text-sm text-zinc-600 dark:text-zinc-400 leading-6">{desc}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-3xl border border-zinc-200 dark:border-zinc-800 bg-white/95 dark:bg-zinc-950/95 p-8 shadow-xl">
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-zinc-950 dark:text-white">{step === 'email' ? '邮箱登录' : '输入验证码'}</h2>
            <p className="mt-2 text-sm text-zinc-500 dark:text-zinc-400">
              {step === 'email'
                ? '输入邮箱后，我们会发送一封包含 6 位验证码的登录邮件。'
                : `验证码已发送到 ${email || '您的邮箱'}，请在 ${expiryMinutes} 分钟内完成验证。`}
            </p>
          </div>

          {step === 'email' ? (
            <form onSubmit={handleRequestCode} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">邮箱地址</label>
                <div className="relative">
                  <Mail className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => {
                      setEmail(e.target.value);
                      setError('');
                    }}
                    placeholder="you@example.com"
                    className="w-full pl-11 pr-4 py-3 rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                    autoComplete="email"
                    autoFocus
                  />
                </div>
                {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
              </div>

              <button
                type="submit"
                disabled={loading || !email.trim()}
                className="w-full py-3 rounded-2xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 font-medium hover:opacity-90 disabled:opacity-50 transition"
              >
                {loading ? '发送中...' : '发送验证码'}
              </button>
              <p className="text-xs text-zinc-500 dark:text-zinc-400">
                验证码发送成功后，这里会自动切换成验证码输入框。
              </p>
            </form>
          ) : (
            <form onSubmit={handleVerifyCode} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-zinc-700 dark:text-zinc-300 mb-2">6 位验证码</label>
                <input
                  type="text"
                  value={code}
                  onChange={(e) => {
                    setCode(e.target.value.replace(/\D/g, '').slice(0, 6));
                    setError('');
                  }}
                  placeholder="请输入 6 位验证码"
                  className="w-full px-4 py-3 rounded-2xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 text-zinc-900 dark:text-white text-center tracking-[0.35em] text-xl focus:outline-none focus:ring-2 focus:ring-zinc-900 dark:focus:ring-white"
                  autoComplete="one-time-code"
                  autoFocus
                />
                {error && <p className="mt-2 text-sm text-red-500">{error}</p>}
                {notice && !error && <p className="mt-2 text-sm text-emerald-600 dark:text-emerald-400">{notice}</p>}
              </div>

              {debugCode && (
                <div className="rounded-2xl border border-sky-200 bg-sky-50 px-4 py-3 text-sm text-sky-700 dark:border-sky-900/60 dark:bg-sky-950/30 dark:text-sky-300">
                  当前处于开发模式，可直接使用验证码：
                  <span className="ml-2 font-mono text-base font-semibold tracking-[0.25em]">{debugCode}</span>
                </div>
              )}

              <button
                type="submit"
                disabled={loading || code.trim().length < 6}
                className="w-full py-3 rounded-2xl bg-zinc-900 text-white dark:bg-white dark:text-zinc-900 font-medium hover:opacity-90 disabled:opacity-50 transition"
              >
                {loading ? '验证中...' : '验证并登录'}
              </button>

              <div className="flex items-center justify-between gap-3 text-sm">
                <button
                  type="button"
                  onClick={handleBack}
                  className="inline-flex items-center gap-1 text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white transition"
                >
                  <ArrowLeft className="w-4 h-4" />
                  返回修改邮箱
                </button>

                <button
                  type="button"
                  onClick={() => {
                    void requestCode();
                  }}
                  disabled={loading || cooldown > 0}
                  className="text-zinc-500 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white disabled:opacity-50 disabled:cursor-not-allowed transition"
                >
                  {cooldown > 0 ? `${cooldown} 秒后可重发` : '重新发送验证码'}
                </button>
              </div>
            </form>
          )}

        </div>
      </div>
    </div>
  );
}
