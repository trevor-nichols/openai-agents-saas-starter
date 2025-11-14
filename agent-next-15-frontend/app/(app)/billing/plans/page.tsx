// File Path: app/(app)/billing/plans/page.tsx
// Description: Placeholder self-serve plan management page.
// Sections:
// - Imports: Billing plan management feature entry point.
// - BillingPlansPage component: Thin wrapper around the plan management view.

import { PlanManagement } from '@/features/billing';

export const metadata = {
  title: 'Billing Plans | Anything Agents',
};

export default function BillingPlansPage() {
  return <PlanManagement />;
}

