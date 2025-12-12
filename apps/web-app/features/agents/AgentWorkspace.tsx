// File Path: features/agents/AgentWorkspace.tsx
// Description: Feature orchestrator composing agent roster, chat, conversations, and tooling insights.

'use client';

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

import { SectionHeader } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';
import { Button } from '@/components/ui/button';
import { useChatController } from '@/lib/chat';
import { useAgentStatuses } from '@/lib/queries/agents';

import { AGENT_WORKSPACE_COPY } from './constants';
import { useAgentWorkspaceData } from './hooks/useAgentWorkspaceData';
import { AgentCatalogGrid } from './components/AgentCatalogGrid';
import { AgentWorkspaceChatPanel } from './components/AgentWorkspaceChatPanel';
import { ConversationArchivePanel } from './components/ConversationArchivePanel';
import { AgentToolsPanel } from './components/AgentToolsPanel';
import { ContainerBindingsPanel } from './components/ContainerBindingsPanel';
import { useCreateContainer, useDeleteContainer, useBindAgentContainer, useUnbindAgentContainer } from '@/lib/queries/containers';

export function AgentWorkspace() {
  const {
    agentsPages,
    agents,
    agentsTotal,
    isLoadingAgents,
    agentsError,
    hasNextAgentsPage,
    fetchNextAgentsPage,
    isFetchingNextAgentsPage,
    refetchAgents,
    containers,
    isLoadingContainers,
    containersError,
    toolsSummary,
    toolsByAgent,
    isLoadingTools,
    toolsError,
    refetchTools,
    conversationList,
    isLoadingConversations,
    conversationsError,
    loadConversations,
    loadMoreConversations,
    hasNextConversationPage,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
  } = useAgentWorkspaceData();

  const [pageIndex, setPageIndex] = useState(0);
  const pagesLengthRef = useRef(agentsPages.length);

  useEffect(() => {
    pagesLengthRef.current = agentsPages.length;
  }, [agentsPages.length]);

  const clampedPageIndex = useMemo(() => {
    if (agentsPages.length === 0) {
      return 0;
    }
    return Math.min(pageIndex, agentsPages.length - 1);
  }, [agentsPages.length, pageIndex]);

  const statusQuery = useAgentStatuses(agents.map((agent) => agent.name));

  const agentsWithStatus = useMemo(
    () =>
      agents.map((agent) => ({
        ...agent,
        last_seen_at: statusQuery.statusMap[agent.name]?.last_used ?? agent.last_seen_at ?? null,
      })),
    [agents, statusQuery.statusMap],
  );

  const pagedAgentsWithStatus = useMemo(
    () =>
      agentsPages.map((page) => ({
        ...page,
        items: (page.items ?? []).map((agent) => ({
          ...agent,
          last_seen_at: statusQuery.statusMap[agent.name]?.last_used ?? agent.last_seen_at ?? null,
        })),
      })),
    [agentsPages, statusQuery.statusMap],
  );

  const pageCount = pagedAgentsWithStatus.length;
  const hasPrevPage = clampedPageIndex > 0;
  const canAdvanceLoadedPage = clampedPageIndex < pageCount - 1;
  const rosterErrorMessage = agentsError?.message ?? statusQuery.statusError?.message ?? toolsError;
  const rosterLoading = isLoadingAgents || statusQuery.isLoadingStatuses;

  const handleNextPage = useCallback(async () => {
    if (canAdvanceLoadedPage) {
      setPageIndex((idx) => Math.min(idx + 1, pageCount - 1));
      return;
    }
    if (!hasNextAgentsPage || isFetchingNextAgentsPage) {
      return;
    }
    const result = await fetchNextAgentsPage();
    const nextLength = result.data?.pages?.length ?? pagesLengthRef.current;
    if (nextLength > pageCount) {
      setPageIndex((idx) => Math.min(idx + 1, nextLength - 1));
    }
  }, [canAdvanceLoadedPage, fetchNextAgentsPage, hasNextAgentsPage, isFetchingNextAgentsPage, pageCount]);

  const handlePrevPage = useCallback(() => {
    if (!hasPrevPage) {
      return;
    }
    setPageIndex((idx) => Math.max(idx - 1, 0));
  }, [hasPrevPage]);

  const handleCarouselSelect = useCallback(
    async (nextIndex: number) => {
      if (nextIndex === clampedPageIndex) {
        return;
      }
      if (nextIndex < clampedPageIndex) {
        setPageIndex(Math.max(0, nextIndex));
        return;
      }

      // Attempting to move forward
      if (nextIndex < pageCount) {
        setPageIndex(Math.min(nextIndex, pageCount - 1));
        return;
      }

      if (!hasNextAgentsPage || isFetchingNextAgentsPage) {
        return;
      }

      const result = await fetchNextAgentsPage();
      const nextLength = result.data?.pages?.length ?? pagesLengthRef.current;
      if (nextLength > clampedPageIndex) {
        setPageIndex(() => Math.min(nextIndex, nextLength - 1));
      }
    },
    [clampedPageIndex, fetchNextAgentsPage, hasNextAgentsPage, isFetchingNextAgentsPage, pageCount],
  );

  const chatController = useChatController({
    onConversationAdded: addConversationToList,
    onConversationUpdated: updateConversationInList,
    onConversationRemoved: removeConversationFromList,
    reloadConversations: loadConversations,
  });

  const {
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    sendMessage,
    selectConversation,
    startNewConversation,
    deleteConversation,
    clearError,
  } = chatController;

  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [detailConversationId, setDetailConversationId] = useState<string | null>(null);
  const [insightsOpen, setInsightsOpen] = useState(false);
  const [insightsTab, setInsightsTab] = useState<'archive' | 'tools' | 'containers'>('archive');
  const [selectedContainerId, setSelectedContainerId] = useState<string | null>(null);

  const createContainer = useCreateContainer();
  const deleteContainer = useDeleteContainer();
  const bindContainer = useBindAgentContainer(selectedAgent);
  const unbindContainer = useUnbindAgentContainer(selectedAgent);

  const handleSelectConversationFromArchive = useCallback(
    (conversationId: string) => {
      setDetailConversationId(conversationId);
      setDetailDrawerOpen(true);
      void selectConversation(conversationId);
    },
    [selectConversation],
  );

  const handleShowCurrentConversation = useCallback(() => {
    if (!currentConversationId) {
      return;
    }
    setDetailConversationId(currentConversationId);
    setDetailDrawerOpen(true);
  }, [currentConversationId]);

  const handleConversationDeleted = useCallback(
    (conversationId: string) => {
      loadConversations();
      if (detailConversationId === conversationId) {
        setDetailDrawerOpen(false);
        setDetailConversationId(null);
      }
      if (currentConversationId === conversationId) {
        startNewConversation();
      }
    },
    [
      currentConversationId,
      detailConversationId,
      loadConversations,
      startNewConversation,
    ],
  );

  const handleSelectAgent = useCallback(
    (agentName: string) => {
      if (agentName === selectedAgent) {
        return;
      }
      setSelectedAgent(agentName);
      startNewConversation();
    },
    [selectedAgent, setSelectedAgent, startNewConversation],
  );

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={AGENT_WORKSPACE_COPY.eyebrow}
        title={AGENT_WORKSPACE_COPY.title}
        description={AGENT_WORKSPACE_COPY.description}
      />

      <div className="grid gap-8 xl:grid-cols-[minmax(520px,1.1fr)_minmax(640px,1fr)]">
        <AgentCatalogGrid
          agentsPages={pagedAgentsWithStatus}
          visiblePageIndex={clampedPageIndex}
          totalAgents={agentsTotal}
          hasNextPage={hasNextAgentsPage}
          hasPrevPage={hasPrevPage}
          onNextPage={handleNextPage}
          onPrevPage={handlePrevPage}
          onPageSelect={handleCarouselSelect}
          toolsByAgent={toolsByAgent}
          summary={toolsSummary}
          isLoadingAgents={rosterLoading}
          isFetchingNextPage={isFetchingNextAgentsPage}
          isLoadingTools={isLoadingTools}
          errorMessage={rosterErrorMessage}
          onRefreshTools={refetchTools}
          onRefreshAgents={() => refetchAgents().then(() => undefined)}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
        />

        <AgentWorkspaceChatPanel
          agents={agentsWithStatus}
          agentsError={agentsError}
          isLoadingAgents={rosterLoading}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
          currentConversationId={currentConversationId}
          onClearError={clearError}
          onSendMessage={sendMessage}
          onStartNewConversation={startNewConversation}
          onShowConversationDetail={handleShowCurrentConversation}
          chatController={chatController}
        />
      </div>

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
              onValueChange={(value) => setInsightsTab(value as 'archive' | 'tools' | 'containers')}
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
                  onRefresh={loadConversations}
                  onLoadMore={loadMoreConversations}
                  hasNextPage={hasNextConversationPage}
                  onSelectConversation={handleSelectConversationFromArchive}
                />
              </TabsContent>

              <TabsContent value="tools" className="space-y-4">
                <AgentToolsPanel
                  summary={toolsSummary}
                  toolsByAgent={toolsByAgent}
                  selectedAgent={selectedAgent}
                  isLoading={isLoadingTools}
                  error={toolsError}
                  onRefresh={refetchTools}
                />
              </TabsContent>

              <TabsContent value="containers" className="space-y-4">
                <ContainerBindingsPanel
                  containers={containers}
                  isLoading={isLoadingContainers}
                  error={containersError}
                  selectedContainerId={selectedContainerId}
                  onSelect={setSelectedContainerId}
                  onCreate={(name, memory) => createContainer.mutate({ name, memory_limit: memory ?? null })}
                  onDelete={(id) => deleteContainer.mutate(id)}
                  onBind={(id) => bindContainer.mutate(id)}
                  onUnbind={() => unbindContainer.mutate()}
                  agentKey={selectedAgent}
                />
              </TabsContent>
            </Tabs>
          </div>
        </div>
      ) : null}

      <ConversationDetailDrawer
        conversationId={detailConversationId}
        open={detailDrawerOpen}
        onClose={() => setDetailDrawerOpen(false)}
        onDeleted={handleConversationDeleted}
        onDeleteConversation={deleteConversation}
      />
    </section>
  );
}
