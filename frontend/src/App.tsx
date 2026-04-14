import { useCallback, useEffect, useState } from 'react';
import { api } from './api';
import AdminPortal from './components/AdminPortal';
import EmailLogin from './components/EmailLogin';
import UserWorkspace from './components/UserWorkspace';
import type { SessionResponse } from './types';

const USER_SESSION_STORAGE_KEY = 'user_session_token';

type AppRoute = 'user' | 'admin';

function getCurrentRoute(): AppRoute {
  return window.location.pathname.startsWith('/admin') ? 'admin' : 'user';
}

function App() {
  const [route, setRoute] = useState<AppRoute>(getCurrentRoute);
  const [checkingSession, setCheckingSession] = useState(true);
  const [session, setSession] = useState<SessionResponse | null>(null);

  const applySession = useCallback((payload: SessionResponse | null) => {
    if (payload) {
      localStorage.setItem(USER_SESSION_STORAGE_KEY, payload.session_token);
      localStorage.removeItem('license_code');
      setSession(payload);
      return;
    }

    localStorage.removeItem(USER_SESSION_STORAGE_KEY);
    localStorage.removeItem('license_code');
    setSession(null);
  }, []);

  const refreshSession = useCallback(async () => {
    const token = localStorage.getItem(USER_SESSION_STORAGE_KEY);
    if (!token) {
      setSession(null);
      setCheckingSession(false);
      return;
    }

    try {
      const payload = await api.getSessionMe();
      applySession(payload);
    } catch {
      applySession(null);
    } finally {
      setCheckingSession(false);
    }
  }, [applySession]);

  useEffect(() => {
    const syncRoute = () => setRoute(getCurrentRoute());
    window.addEventListener('popstate', syncRoute);
    return () => window.removeEventListener('popstate', syncRoute);
  }, []);

  useEffect(() => {
    refreshSession();
  }, [refreshSession]);

  if (route === 'admin') {
    return <AdminPortal />;
  }

  if (checkingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[var(--color-background)]">
        <div className="w-8 h-8 border-2 border-zinc-300 border-t-zinc-900 dark:border-zinc-700 dark:border-t-white rounded-full animate-spin" />
      </div>
    );
  }

  if (!session) {
    return <EmailLogin onLogin={applySession} />;
  }

  return (
    <UserWorkspace
      session={session}
      onSessionChange={applySession}
      onLogout={() => applySession(null)}
    />
  );
}

export default App;
