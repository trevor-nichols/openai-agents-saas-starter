// File Path: app/(app)/settings/tenant/page.tsx
// Description: Placeholder tenant settings page.
// Sections:
// - Imports: Settings feature orchestrator.
// - TenantSettingsPage component: Thin wrapper for the tenant settings view.

import { TenantSettingsPanel } from '@/features/settings';

export const metadata = {
  title: 'Tenant Settings | Anything Agents',
};

export default function TenantSettingsPage() {
  return <TenantSettingsPanel />;
}

