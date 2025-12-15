// File Path: features/agents/components/AgentWorkspaceInsights.tsx
// Description: Collapsible insights section for conversations, tools, and container bindings.

'use client';

import { useState } from 'react';
import { Archive, Box, Wrench } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from '@/components/ui/sheet';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import type { ContainerResponse } from '@/lib/api/client/types.gen';
import type { ConversationListItem } from '@/types/conversations';

import { AgentToolsPanel } from './AgentToolsPanel';
import { ContainerBindingsPanel } from './ContainerBindingsPanel';
import { ConversationArchivePanel } from './ConversationArchivePanel';
import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

interface AgentWorkspaceInsightsProps {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  isFetchingMoreConversations: boolean;
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
  isFetchingMoreConversations,
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

  const openTab = (tab: typeof insightsTab) => {
    setInsightsTab(tab);
    setInsightsOpen(true);
  };

  return (
    <>
      <div className="flex flex-col gap-4">
        <Separator />
        <div className="flex flex-col gap-2">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Workspace Insights
          </h4>
          <div className="grid grid-cols-3 gap-2">
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col items-center gap-1 h-auto py-3 text-xs"
              onClick={() => openTab('archive')}
            >
              <Archive className="h-4 w-4 opacity-70" />
              <span>Archive</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col items-center gap-1 h-auto py-3 text-xs"
              onClick={() => openTab('tools')}
            >
              <Wrench className="h-4 w-4 opacity-70" />
              <span>Tools</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="flex flex-col items-center gap-1 h-auto py-3 text-xs"
              onClick={() => openTab('containers')}
            >
              <Box className="h-4 w-4 opacity-70" />
              <span>Containers</span>
            </Button>
          </div>
        </div>
      </div>

      <Sheet open={insightsOpen} onOpenChange={setInsightsOpen}>
        <SheetContent side="bottom" className="h-[85vh] sm:max-h-[85vh]">
          <SheetHeader>
            <SheetTitle>Workspace Insights</SheetTitle>
            <SheetDescription>
              Manage conversation history, inspect tool definitions, and configure sandboxed containers.
            </SheetDescription>
          </SheetHeader>
          
          <div className="mt-6 h-full pb-12">
            <Tabs
              value={insightsTab}
              onValueChange={(value) =>
                setInsightsTab(value as 'archive' | 'tools' | 'containers')
              }
              className="flex h-full flex-col gap-4"
            >
              <TabsList>
                <TabsTrigger value="archive" className="gap-2">
                  <Archive className="h-4 w-4" /> Archive
                </TabsTrigger>
                <TabsTrigger value="tools" className="gap-2">
                  <Wrench className="h-4 w-4" /> Tools
                </TabsTrigger>
                <TabsTrigger value="containers" className="gap-2">
                  <Box className="h-4 w-4" /> Containers
                </TabsTrigger>
              </TabsList>

              <TabsContent value="archive" className="flex-1 overflow-hidden p-1">
                <ConversationArchivePanel
                  conversationList={conversationList}
                  isLoading={isLoadingConversations}
                  isLoadingMore={isFetchingMoreConversations}
                  error={conversationsError}
                  onRefresh={onRefreshConversations}
                  onLoadMore={onLoadMoreConversations}
                  hasNextPage={hasNextConversationPage}
                  onSelectConversation={(id) => {
                    onSelectConversation(id);
                    setInsightsOpen(false);
                  }}
                />
              </TabsContent>

              <TabsContent value="tools" className="flex-1 overflow-y-auto p-1">
                <AgentToolsPanel
                  summary={toolsSummary}
                  toolsByAgent={toolsByAgent}
                  selectedAgent={selectedAgent}
                  isLoading={isLoadingTools}
                  error={toolsError}
                  onRefresh={onRefreshTools}
                />
              </TabsContent>

              <TabsContent value="containers" className="flex-1 overflow-y-auto p-1">
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
        </SheetContent>
      </Sheet>
    </>
  );
}
