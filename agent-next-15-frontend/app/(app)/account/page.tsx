// File Path: app/(app)/account/page.tsx
// Description: Unified account surface with tabbed navigation for profile, security, and sessions.
// Sections:
// - Imports & helpers
// - AccountPage component: normalizes the requested tab and renders the overview

import { AccountOverview } from '@/features/account';

const TAB_KEYS = new Set(['profile', 'security', 'sessions', 'automation']);

interface AccountPageProps {
  searchParams?: {
    tab?: string;
  };
}

function normalizeTab(value?: string | null): string {
  if (!value) return 'profile';
  return TAB_KEYS.has(value) ? value : 'profile';
}

export const metadata = {
  title: 'Account | Anything Agents',
};

export default function AccountPage({ searchParams }: AccountPageProps) {
  const initialTab = normalizeTab(searchParams?.tab);
  return <AccountOverview initialTab={initialTab} />;
}
