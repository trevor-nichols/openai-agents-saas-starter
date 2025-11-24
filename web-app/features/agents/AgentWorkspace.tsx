// File Path: features/agents/AgentWorkspace.tsx
// Description: Feature orchestrator composing agent roster, chat, conversations, and tooling insights.

'use client';

import { useCallback, useState } from 'react';

import { SectionHeader } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ConversationDetailDrawer } from '@/components/shared/conversations/ConversationDetailDrawer';
import { useChatController } from '@/lib/chat/useChatController';

import { AGENT_WORKSPACE_COPY } from './constants';
import { useAgentWorkspaceData } from './hooks/useAgentWorkspaceData';
import { AgentCatalogGrid } from './components/AgentCatalogGrid';
import { AgentWorkspaceChatPanel } from './components/AgentWorkspaceChatPanel';
import { ConversationArchivePanel } from './components/ConversationArchivePanel';
import { AgentToolsPanel } from './components/AgentToolsPanel';

export function AgentWorkspace() {
  const {
    agents,
    isLoadingAgents,
    agentsError,
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

  const {
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    activeAgent,
    toolEvents,
    reasoningText,
    lifecycleStatus,
    sendMessage,
    selectConversation,
    startNewConversation,
    deleteConversation,
    clearError,
  } = useChatController({
    onConversationAdded: addConversationToList,
    onConversationUpdated: updateConversationInList,
    onConversationRemoved: removeConversationFromList,
    reloadConversations: loadConversations,
  });

  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [detailConversationId, setDetailConversationId] = useState<string | null>(null);
  const [insightsOpen, setInsightsOpen] = useState(false);
  const [insightsTab, setInsightsTab] = useState<'archive' | 'tools'>('archive');

  const rosterErrorMessage = agentsError?.message ?? toolsError;

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
          agents={agents}
          toolsByAgent={toolsByAgent}
          summary={toolsSummary}
          isLoadingAgents={isLoadingAgents}
          isLoadingTools={isLoadingTools}
          errorMessage={rosterErrorMessage}
          onRefreshTools={refetchTools}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
        />

        <AgentWorkspaceChatPanel
          agents={agents}
          agentsError={agentsError}
          isLoadingAgents={isLoadingAgents}
          selectedAgent={selectedAgent}
          onSelectAgent={handleSelectAgent}
          messages={messages}
        isSending={isSending}
        isLoadingHistory={isLoadingHistory}
        isClearingConversation={isClearingConversation}
        currentConversationId={currentConversationId}
        errorMessage={errorMessage}
        onClearError={clearError}
        onSendMessage={sendMessage}
        onStartNewConversation={startNewConversation}
        onShowConversationDetail={handleShowCurrentConversation}
        activeAgent={activeAgent}
        tools={toolEvents}
        reasoningText={reasoningText}
        lifecycleStatus={lifecycleStatus}
      />
    </div>

      <div className="flex justify-start">
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => {
              setInsightsOpen(true);
              setInsightsTab('archive');
            }}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-foreground/80 transition hover:bg-white/10"
          >
            View archive
          </button>
          <button
            type="button"
            onClick={() => {
              setInsightsOpen(true);
              setInsightsTab('tools');
            }}
            className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-sm font-medium text-foreground/80 transition hover:bg-white/10"
          >
            View tools
          </button>
        </div>
      </div>

      {insightsOpen ? (
        <div className="mt-10 border-t border-white/10 pt-6 lg:mt-12 lg:pt-8">
          <div className="rounded-2xl border border-white/10 bg-background/70 p-4 shadow-lg shadow-black/20 backdrop-blur">
            <Tabs
              value={insightsTab}
              onValueChange={(value) => setInsightsTab(value as 'archive' | 'tools')}
              className="space-y-4"
            >
              <TabsList className="w-full max-w-md">
                <TabsTrigger value="archive">Conversation archive</TabsTrigger>
                <TabsTrigger value="tools">Agent tools</TabsTrigger>
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
