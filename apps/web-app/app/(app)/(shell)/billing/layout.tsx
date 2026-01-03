import { notFound } from 'next/navigation';

import { isBillingEnabled } from '@/lib/server/features';

export default async function BillingLayout({ children }: { children: React.ReactNode }) {
  if (!(await isBillingEnabled())) {
    notFound();
  }

  return children;
}
