// File Path: features/agents/AgentWorkspace.tsx
// Description: Feature orchestrator composing agent roster, chat, conversations, and tooling insights.

'use client';

import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';
import { SectionHeader } from '@/components/ui/foundation';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';
import { ScrollArea } from '@/components/ui/scroll-area';

import { AgentCatalogGrid } from './components/AgentCatalogGrid';
import { AgentWorkspaceChatPanel } from './components/AgentWorkspaceChatPanel';
import { AgentWorkspaceInsights } from './components/AgentWorkspaceInsights';
import { AGENT_WORKSPACE_COPY } from './constants';
import { useAgentWorkspace } from './hooks/useAgentWorkspace';

export function AgentWorkspace() {
  const { rosterProps, chatProps, insightsProps, drawerProps } = useAgentWorkspace();

  return (
    <section className="flex h-[calc(100vh-4rem)] flex-col space-y-4">
      <div className="px-6 pt-4">
        <SectionHeader
          eyebrow={AGENT_WORKSPACE_COPY.eyebrow}
          title={AGENT_WORKSPACE_COPY.title}
          description={AGENT_WORKSPACE_COPY.description}
          size="compact"
        />
      </div>

      <ResizablePanelGroup direction="horizontal" className="flex-1 overflow-hidden border-t">
        <ResizablePanel defaultSize={35} minSize={25} maxSize={45} className="bg-muted/5">
          <ScrollArea className="h-full">
            <div className="p-6">
              <AgentCatalogGrid {...rosterProps} />
              <div className="mt-8">
                <AgentWorkspaceInsights {...insightsProps} />
              </div>
            </div>
          </ScrollArea>
        </ResizablePanel>
        
        <ResizableHandle withHandle />
        
        <ResizablePanel defaultSize={65} className="bg-background">
          <div className="h-full p-6">
            <AgentWorkspaceChatPanel {...chatProps} />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>

      <ConversationDetailDrawer {...drawerProps} />
    </section>
  );
}
