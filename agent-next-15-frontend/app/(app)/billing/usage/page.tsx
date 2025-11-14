import type { Metadata } from 'next';

import { UsageLedger } from '@/features/billing';

export const metadata: Metadata = {
  title: 'Billing Usage | Anything Agents',
  description: 'Review metered usage entries for your Anything Agents tenant.',
};

export default function BillingUsagePage() {
  return <UsageLedger />;
}
