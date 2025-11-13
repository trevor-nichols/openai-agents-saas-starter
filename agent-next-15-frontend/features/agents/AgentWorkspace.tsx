// File Path: features/agents/AgentWorkspace.tsx
// Description: Feature orchestrator composing agent roster, chat, conversations, and tooling insights.

'use client';

import { useCallback, useMemo, useState } from 'react';

import { SectionHeader } from '@/components/ui/foundation';
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

  const insightsColumn = useMemo(
    () => (
      <div className="space-y-6">
        <ConversationArchivePanel
          conversationList={conversationList}
          isLoading={isLoadingConversations}
          error={conversationsError}
          onRefresh={loadConversations}
          onSelectConversation={handleSelectConversationFromArchive}
        />
        <AgentToolsPanel
          summary={toolsSummary}
          toolsByAgent={toolsByAgent}
          selectedAgent={selectedAgent}
          isLoading={isLoadingTools}
          error={toolsError}
          onRefresh={refetchTools}
        />
      </div>
    ),
    [
      conversationList,
      conversationsError,
      handleSelectConversationFromArchive,
      isLoadingConversations,
      isLoadingTools,
      refetchTools,
      selectedAgent,
      toolsByAgent,
      toolsError,
      toolsSummary,
      loadConversations,
    ],
  );

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={AGENT_WORKSPACE_COPY.eyebrow}
        title={AGENT_WORKSPACE_COPY.title}
        description={AGENT_WORKSPACE_COPY.description}
      />

      <div className="grid gap-6 xl:grid-cols-[minmax(280px,360px)_minmax(480px,1fr)_minmax(280px,360px)]">
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
        />

        {insightsColumn}
      </div>

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
