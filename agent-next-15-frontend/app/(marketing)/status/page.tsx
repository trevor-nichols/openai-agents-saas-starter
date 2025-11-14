import type { Metadata } from 'next';

import { StatusExperience } from '@/features/marketing';

export const metadata: Metadata = {
  title: 'Status | Anything Agents',
  description: 'Monitor platform health, uptime metrics, and incidents for the Anything Agents starter.',
};

export default function StatusPage() {
  return <StatusExperience />;
}
