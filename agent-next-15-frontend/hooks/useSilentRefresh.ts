'use client';

import { useEffect, useRef } from 'react';

interface SessionResponse {
  expiresAt: string;
}

const SAFETY_WINDOW_MS = 60_000;

export function useSilentRefresh() {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let cancelled = false;

    const scheduleRefresh = (expiresAt: string) => {
      const target = new Date(expiresAt).getTime() - SAFETY_WINDOW_MS;
      const delay = Math.max(target - Date.now(), 5_000);
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      timerRef.current = setTimeout(refreshSession, delay);
    };

    const redirectToLogin = () => {
      window.location.href = '/login';
    };

    const refreshSession = async (): Promise<boolean> => {
      try {
        const response = await fetch('/api/auth/refresh', { method: 'POST' });
        if (!response.ok) {
          if (response.status === 401) {
            redirectToLogin();
          }
          return false;
        }
        const data = (await response.json()) as SessionResponse;
        if (!cancelled && data?.expiresAt) {
          scheduleRefresh(data.expiresAt);
        }
        return true;
      } catch (error) {
        console.error('[auth] Silent refresh failed', error);
        redirectToLogin();
        return false;
      }
    };

    const bootstrap = async () => {
      try {
        const session = await fetch('/api/auth/session', { cache: 'no-store' });
        if (!session.ok) {
          if (session.status === 401) {
            await refreshSession();
          }
          return;
        }
        const data = (await session.json()) as SessionResponse;
        if (!cancelled && data?.expiresAt) {
          scheduleRefresh(data.expiresAt);
        }
      } catch (error) {
        console.error('[auth] Failed to bootstrap session', error);
      }
    };

    bootstrap();

    return () => {
      cancelled = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);
}
