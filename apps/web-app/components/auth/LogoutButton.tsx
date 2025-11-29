'use client';

import { useTransition } from 'react';

/**
 * Lightweight client-side trigger that delegates the actual logout
 * to the server-side Route Handler (/api/auth/logout). This keeps
 * cookie mutation on the server and avoids the Next.js cookie
 * restriction seen when calling server actions directly in the
 * client event loop.
 */
export function LogoutButton() {
  const [isPending, startTransition] = useTransition();

  const handleLogout = () => {
    startTransition(async () => {
      try {
        await fetch('/api/auth/logout', { method: 'POST', cache: 'no-store' });
      } catch (error) {
        console.error('[auth] Logout request failed', error);
      } finally {
        window.location.href = '/login';
      }
    });
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={isPending}
      className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 disabled:opacity-60"
    >
      {isPending ? 'Signing out…' : 'Log out'}
    </button>
  );
}
