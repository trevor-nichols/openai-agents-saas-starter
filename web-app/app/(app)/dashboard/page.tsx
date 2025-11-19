// File Path: app/(app)/dashboard/page.tsx
// Description: Placeholder dashboard surface for authenticated users.
// Sections:
// - Imports: Feature orchestrator.
// - DashboardPage: Thin wrapper around the dashboard feature.

import { DashboardOverview } from '@/features/dashboard';

export const metadata = {
  title: 'Dashboard | Acme',
};

export default function DashboardPage() {
  return <DashboardOverview />;
}

