import { redirect } from 'next/navigation';

import { Suspense } from 'react';

import { TeamSettingsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { isTenantAdmin } from '@/lib/auth/roles';

export const metadata = {
  title: 'Team Settings | Acme',
};

export default function TeamSettingsPage() {
  return (
    <Suspense fallback={null}>
      <TeamSettingsContent />
    </Suspense>
  );
}

async function TeamSettingsContent() {
  const session = await getSessionMetaFromCookies();
  const scopes = session?.scopes ?? [];

  if (!session?.tenantId || !isTenantAdmin({ scopes })) {
    redirect('/dashboard');
  }

  return <TeamSettingsWorkspace />;
}
