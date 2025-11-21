import type { Metadata } from 'next';

import { AccessRequestExperience } from '@/features/marketing';

export const metadata: Metadata = {
  title: 'Request access · Acme',
  description:
    'Share your use case and our operators will send an invite token or approval decision for the Acme starter.',
};

export default function RequestAccessPage() {
  return <AccessRequestExperience />;
}
