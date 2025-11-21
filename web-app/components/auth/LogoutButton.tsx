'use client';

import { useTransition } from 'react';

import { logoutAction } from '@/app/actions/auth';

export function LogoutButton() {
  const [isPending, startTransition] = useTransition();

  const handleLogout = () => {
    startTransition(() => {
      void logoutAction();
    });
  };

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={isPending}
      className="px-3 py-1.5 text-sm rounded-md border border-gray-300 text-gray-700 hover:bg-gray-200 disabled:opacity-60"
    >
      {isPending ? 'Signing out…' : 'Logout'}
    </button>
  );
}
