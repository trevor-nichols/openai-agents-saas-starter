import { redirect } from 'next/navigation';

import { TenantSettingsWorkspace } from '@/features/settings';
import { getSessionMetaFromCookies } from '@/lib/auth/cookies';

export const metadata = {
  title: 'Tenant Settings | Anything Agents',
};

export default async function TenantSettingsPage() {
  const session = await getSessionMetaFromCookies();
  const scopes = session?.scopes ?? [];
  const canManageBilling = scopes.includes('billing:manage');

  if (!session?.tenantId || !canManageBilling) {
    redirect('/dashboard');
  }

  return <TenantSettingsWorkspace />;
}
