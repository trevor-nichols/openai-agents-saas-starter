// File Path: app/(app)/billing/page.tsx
// Description: Placeholder billing overview page.
// Sections:
// - Imports: Billing feature orchestrator.
// - BillingPage component: Thin wrapper around the billing overview.

import { BillingOverview } from '@/features/billing';

export const metadata = {
  title: 'Billing | Anything Agents',
};

export default function BillingPage() {
  return <BillingOverview />;
}

