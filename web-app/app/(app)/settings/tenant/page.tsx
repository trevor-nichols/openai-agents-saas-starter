import { redirect } from 'next/navigation';

import { Suspense } from 'react';

import { TenantSettingsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';

export const metadata = {
  title: 'Tenant Settings | Acme',
};

export default function TenantSettingsPage() {
  return (
    <Suspense fallback={null}>
      <TenantSettingsContent />
    </Suspense>
  );
}

async function TenantSettingsContent() {
  const session = await getSessionMetaFromCookies();
  const scopes = session?.scopes ?? [];
  const canManageBilling = scopes.includes('billing:manage');

  if (!session?.tenantId || !canManageBilling) {
    redirect('/dashboard');
  }

  return <TenantSettingsWorkspace />;
}
