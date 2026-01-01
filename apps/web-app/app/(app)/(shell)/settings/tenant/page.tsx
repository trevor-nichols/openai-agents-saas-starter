import { redirect } from 'next/navigation';

import { Suspense } from 'react';

import { TenantSettingsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { isTenantAdmin, isTenantAdminRole } from '@/lib/auth/roles';
import { getCurrentUserProfile } from '@/lib/server/services/users';

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
  let role: string | null = null;
  if (session) {
    try {
      const profile = await getCurrentUserProfile();
      role = profile?.role ?? null;
    } catch {
      role = null;
    }
  }
  const canManageTenant = isTenantAdmin({ role, scopes });
  const canManageTenantAccount = isTenantAdminRole(role);
  const canManageTenantSettings = canManageTenant;

  if (!session?.tenantId || !canManageTenant) {
    redirect('/dashboard');
  }

  return (
    <TenantSettingsWorkspace
      canManageBilling={canManageBilling}
      canManageTenantSettings={canManageTenantSettings}
      canManageTenantAccount={canManageTenantAccount}
    />
  );
}
