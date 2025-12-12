// File Path: features/agents/AgentWorkspace.tsx
// Description: Feature orchestrator composing agent roster, chat, conversations, and tooling insights.

'use client';

import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';
import { SectionHeader } from '@/components/ui/foundation';

import { AgentCatalogGrid } from './components/AgentCatalogGrid';
import { AgentWorkspaceChatPanel } from './components/AgentWorkspaceChatPanel';
import { AgentWorkspaceInsights } from './components/AgentWorkspaceInsights';
import { AGENT_WORKSPACE_COPY } from './constants';
import { useAgentWorkspace } from './hooks/useAgentWorkspace';

export function AgentWorkspace() {
  const { rosterProps, chatProps, insightsProps, drawerProps } = useAgentWorkspace();

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={AGENT_WORKSPACE_COPY.eyebrow}
        title={AGENT_WORKSPACE_COPY.title}
        description={AGENT_WORKSPACE_COPY.description}
      />

      <div className="grid gap-8 xl:grid-cols-[minmax(520px,1.1fr)_minmax(640px,1fr)]">
        <AgentCatalogGrid {...rosterProps} />
        <AgentWorkspaceChatPanel {...chatProps} />
      </div>

      <AgentWorkspaceInsights {...insightsProps} />
      <ConversationDetailDrawer {...drawerProps} />
    </section>
  );
}
