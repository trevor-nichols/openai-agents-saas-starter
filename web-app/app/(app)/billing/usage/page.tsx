import type { Metadata } from 'next';

import { UsageLedger } from '@/features/billing';

export const metadata: Metadata = {
  title: 'Billing Usage | Acme',
  description: 'Review metered usage entries for your Acme tenant.',
};

export default function BillingUsagePage() {
  return <UsageLedger />;
}
