import { redirect } from 'next/navigation';

import { Suspense } from 'react';

import { TeamSettingsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { isTenantAdmin } from '@/lib/auth/roles';
import { getTeamInvitePolicy } from '@/lib/server/services/team';

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

  let invitePolicy = null;
  try {
    invitePolicy = await getTeamInvitePolicy();
  } catch (error) {
    console.error('[settings] Failed to load team invite policy', error);
  }

  return <TeamSettingsWorkspace invitePolicy={invitePolicy} />;
}
