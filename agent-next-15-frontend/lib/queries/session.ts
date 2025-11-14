/**
 * Session management hook
 *
 * Note: This uses a custom hook pattern because it manages:
 * - Timer-based automatic refresh
 * - Side effects (redirects)
 * - Lifecycle management (bootstrap, cleanup)
 *
 * These patterns don't fit well into TanStack Query's request-response model.
 */

'use client';

import { useEffect, useRef } from 'react';

import { fetchSession, refreshSession, redirectToLogin } from '@/lib/api/session';

/**
 * Safety window before token expiration to trigger refresh
 * Refreshes 60 seconds before actual expiration
 */
const SAFETY_WINDOW_MS = 60_000;

/**
 * Minimum delay between refresh attempts
 */
const MIN_DELAY_MS = 5_000;

/**
 * Hook to automatically refresh user session before expiration
 *
 * Features:
 * - Bootstraps on mount by checking current session
 * - Schedules automatic refresh before token expiration
 * - Redirects to login on auth failure
 * - Proper cleanup on unmount
 *
 * Usage: Simply call this hook in your root layout or app component
 */
export function useSilentRefresh(): void {
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let cancelled = false;

    /**
     * Schedule the next refresh based on token expiration time
     */
    const scheduleRefresh = (expiresAt: string) => {
      const target = new Date(expiresAt).getTime() - SAFETY_WINDOW_MS;
      const delay = Math.max(target - Date.now(), MIN_DELAY_MS);

      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      console.log(`[auth] Scheduling refresh in ${Math.round(delay / 1000)}s`);
      timerRef.current = setTimeout(handleRefresh, delay);
    };

    /**
     * Perform session refresh and schedule next one
     */
    const handleRefresh = async (): Promise<boolean> => {
      try {
        const data = await refreshSession();

        if (!cancelled && data?.expiresAt) {
          console.log('[auth] Session refreshed successfully');
          scheduleRefresh(data.expiresAt);
        }

        return true;
      } catch (error) {
        console.error('[auth] Silent refresh failed', error);
        redirectToLogin();
        return false;
      }
    };

    /**
     * Bootstrap: Check current session and schedule first refresh
     */
    const bootstrap = async () => {
      try {
        const data = await fetchSession();

        if (!cancelled && data?.expiresAt) {
          console.log('[auth] Session bootstrap successful');
          scheduleRefresh(data.expiresAt);
        }
      } catch (error) {
        // Session check failed, try refreshing
        console.warn('[auth] Session check failed, attempting refresh', error);
        await handleRefresh();
      }
    };

    bootstrap();

    // Cleanup on unmount
    return () => {
      cancelled = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, []);
}
