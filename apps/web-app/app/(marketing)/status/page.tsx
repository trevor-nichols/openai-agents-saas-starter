import type { Metadata } from 'next';

import { StatusExperience } from '@/features/marketing';

export const metadata: Metadata = {
  title: 'Status | Acme',
  description: 'Monitor platform health, uptime metrics, and incidents for the Acme starter.',
};

export default function StatusPage() {
  return <StatusExperience />;
}
