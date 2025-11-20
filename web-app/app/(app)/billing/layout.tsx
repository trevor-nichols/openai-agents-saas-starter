import { notFound } from 'next/navigation';

import { billingEnabled } from '@/lib/config/features';

export default function BillingLayout({ children }: { children: React.ReactNode }) {
  if (!billingEnabled) {
    notFound();
  }

  return children;
}
