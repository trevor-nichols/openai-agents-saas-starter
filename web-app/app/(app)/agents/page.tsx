// File Path: app/(app)/agents/page.tsx
// Description: Thin page shell that renders the consolidated agent workspace.
// Sections:
// - Imports: Feature orchestrator.
// - AgentsPage component: Thin wrapper around the agents feature.

import { AgentWorkspace } from '@/features/agents';

export const metadata = {
  title: 'Agents | Acme',
};

export default function AgentsPage() {
  return <AgentWorkspace />;
}
