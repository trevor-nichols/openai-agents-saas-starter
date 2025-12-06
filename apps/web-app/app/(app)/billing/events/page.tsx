import { Suspense } from 'react';
import type { Metadata } from 'next';

import { EventsLedger } from '@/features/billing';

export const metadata: Metadata = {
  title: 'Billing Events | Acme',
  description: 'Audit Stripe events, invoices, and usage logs for your tenant.',
};

export default async function BillingEventsPage() {
  return (
    <Suspense fallback={null}>
      <EventsLedger />
    </Suspense>
  );
}
