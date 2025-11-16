import type { Metadata } from 'next';

import { AccessRequestExperience } from '@/features/marketing';

export const metadata: Metadata = {
  title: 'Request access · Anything Agents',
  description:
    'Share your use case and our operators will send an invite token or approval decision for the Anything Agents starter.',
};

export default function RequestAccessPage() {
  return <AccessRequestExperience />;
}
