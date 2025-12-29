import { Suspense } from 'react';
import type { Metadata } from 'next';

import { InvoicesLedger } from '@/features/billing';

export const metadata: Metadata = {
  title: 'Invoices | Acme',
  description: 'Review stored invoices and billing receipts for your tenant.',
};

export default async function BillingInvoicesPage() {
  return (
    <Suspense fallback={null}>
      <InvoicesLedger />
    </Suspense>
  );
}
