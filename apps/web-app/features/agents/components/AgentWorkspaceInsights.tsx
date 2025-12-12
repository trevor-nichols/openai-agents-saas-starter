// File Path: features/agents/components/AgentWorkspaceInsights.tsx
// Description: Collapsible insights section for conversations, tools, and container bindings.

'use client';

import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { ContainerResponse } from '@/lib/api/client/types.gen';
import type { ConversationListItem } from '@/types/conversations';

import { AgentToolsPanel } from './AgentToolsPanel';
import { ContainerBindingsPanel } from './ContainerBindingsPanel';
import { ConversationArchivePanel } from './ConversationArchivePanel';
import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

interface AgentWorkspaceInsightsProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  conversationsError: string | null;
  onRefreshConversations: () => void;
  onLoadMoreConversations: () => void;
  hasNextConversationPage: boolean;
  onSelectConversation: (conversationId: string) => void;

  toolsSummary: ToolRegistrySummary;
  toolsByAgent: ToolsByAgentMap;
  selectedAgent: string | null;
  isLoadingTools: boolean;
  toolsError: string | null;
  onRefreshTools: () => void | Promise<void>;

  containers: ContainerResponse[];
  isLoadingContainers: boolean;
  containersError: Error | null;
  onCreateContainer: (name: string, memoryLimit?: string | null) => void;
  onDeleteContainer: (id: string) => void;
  onBindContainer: (id: string) => void;
  onUnbindContainer: () => void;
}

export function AgentWorkspaceInsights({
  conversationList,
  isLoadingConversations,
  conversationsError,
  onRefreshConversations,
  onLoadMoreConversations,
  hasNextConversationPage,
  onSelectConversation,
  toolsSummary,
  toolsByAgent,
  selectedAgent,
  isLoadingTools,
  toolsError,
  onRefreshTools,
  containers,
  isLoadingContainers,
  containersError,
  onCreateContainer,
  onDeleteContainer,
  onBindContainer,
  onUnbindContainer,
}: AgentWorkspaceInsightsProps) {
  const [insightsOpen, setInsightsOpen] = useState(false);
  const [insightsTab, setInsightsTab] = useState<'archive' | 'tools' | 'containers'>('archive');
  const [selectedContainerId, setSelectedContainerId] = useState<string | null>(null);

  return (
    <>
      <div className="flex justify-start">
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInsightsOpen(true);
              setInsightsTab('archive');
            }}
          >
            View archive
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInsightsOpen(true);
              setInsightsTab('tools');
            }}
          >
            View tools
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              setInsightsOpen(true);
              setInsightsTab('containers');
            }}
          >
            View containers
          </Button>
        </div>
      </div>

      {insightsOpen ? (
        <div className="mt-10 border-t border-white/10 pt-6 lg:mt-12 lg:pt-8">
          <div className="rounded-2xl border border-white/10 bg-background/70 p-4 shadow-lg shadow-black/20 backdrop-blur">
            <Tabs
              value={insightsTab}
              onValueChange={(value) =>
                setInsightsTab(value as 'archive' | 'tools' | 'containers')
              }
              className="space-y-4"
            >
              <TabsList className="w-full max-w-md">
                <TabsTrigger value="archive">Conversation archive</TabsTrigger>
                <TabsTrigger value="tools">Agent tools</TabsTrigger>
                <TabsTrigger value="containers">Containers</TabsTrigger>
              </TabsList>

              <TabsContent value="archive" className="space-y-4">
                <ConversationArchivePanel
                  conversationList={conversationList}
                  isLoading={isLoadingConversations}
                  error={conversationsError}
                  onRefresh={onRefreshConversations}
                  onLoadMore={onLoadMoreConversations}
                  hasNextPage={hasNextConversationPage}
                  onSelectConversation={onSelectConversation}
                />
              </TabsContent>

              <TabsContent value="tools" className="space-y-4">
                <AgentToolsPanel
                  summary={toolsSummary}
                  toolsByAgent={toolsByAgent}
                  selectedAgent={selectedAgent}
                  isLoading={isLoadingTools}
                  error={toolsError}
                  onRefresh={onRefreshTools}
                />
              </TabsContent>

              <TabsContent value="containers" className="space-y-4">
                <ContainerBindingsPanel
                  containers={containers}
                  isLoading={isLoadingContainers}
                  error={containersError}
                  selectedContainerId={selectedContainerId}
                  onSelect={setSelectedContainerId}
                  onCreate={onCreateContainer}
                  onDelete={onDeleteContainer}
                  onBind={onBindContainer}
                  onUnbind={onUnbindContainer}
                  agentKey={selectedAgent ?? ''}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      ) : null}
    </>
  );
}

