// File Path: app/(app)/account/page.tsx
// Description: Unified account surface with tabbed navigation for profile, security, and sessions.
// Sections:
// - Imports & helpers
// - AccountPage component: normalizes the requested tab and renders the overview

import { Suspense } from 'react';

import { AccountOverview } from '@/features/account';

const TAB_KEYS = new Set(['profile', 'security', 'sessions', 'automation']);

interface AccountPageProps {
  searchParams: Promise<{
    tab?: string;
  } | undefined>;
}

function normalizeTab(value?: string | null): string {
  if (!value) return 'profile';
  return TAB_KEYS.has(value) ? value : 'profile';
}

export const metadata = {
  title: 'Account | Acme',
};

export default function AccountPage({ searchParams }: AccountPageProps) {
  return (
    <Suspense fallback={null}>
      <AccountPageContent searchParams={searchParams} />
    </Suspense>
  );
}

async function AccountPageContent({ searchParams }: AccountPageProps) {
  const params = await searchParams;
  const initialTab = normalizeTab(params?.tab);
  return <AccountOverview initialTab={initialTab} />;
}
