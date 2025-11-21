import type { Metadata } from 'next';

import { EventsLedger } from '@/features/billing';

export const metadata: Metadata = {
  title: 'Billing Events | Acme',
  description: 'Audit Stripe events, invoices, and usage logs for your tenant.',
};

export default function BillingEventsPage() {
  return <EventsLedger />;
}
