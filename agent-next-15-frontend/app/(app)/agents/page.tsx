// File Path: app/(app)/agents/page.tsx
// Description: Placeholder page for Agent roster and status telemetry.
// Sections:
// - Imports: Feature orchestrator.
// - AgentsPage component: Thin wrapper around the agents feature.

import { AgentsOverview } from '@/features/agents';

export const metadata = {
  title: 'Agents | Anything Agents',
};

export default function AgentsPage() {
  return <AgentsOverview />;
}

