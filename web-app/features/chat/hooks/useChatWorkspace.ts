'use client';

import { useCallback, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { useChatController } from '@/lib/chat/useChatController';
import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';
import { useTools } from '@/lib/queries/tools';

import { CHAT_COPY } from '../constants';
import { normalizeAgentLabel } from '../utils/formatters';

export function useChatWorkspace() {
  const {
    conversationList,
    isLoadingConversations,
    loadMore,
    hasNextPage,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
    loadConversations,
  } = useConversations();
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const {
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    clearError,
    sendMessage,
    selectConversation,
    startNewConversation,
    deleteConversation,
  } = useChatController({
    onConversationAdded: addConversationToList,
    onConversationUpdated: updateConversationInList,
    onConversationRemoved: removeConversationFromList,
    reloadConversations: loadConversations,
  });
  const { tools, isLoading: isLoadingTools, error: toolsError, refetch: refetchTools } = useTools();

  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [toolDrawerOpen, setToolDrawerOpen] = useState(false);

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const selectedAgentLabel = useMemo(() => normalizeAgentLabel(selectedAgent), [selectedAgent]);

  const handleSelectConversation = useCallback(
    (conversationId: string) => {
      void selectConversation(conversationId);
    },
    [selectConversation],
  );

  const handleNewConversation = useCallback(() => {
    startNewConversation();
  }, [startNewConversation]);

  const handleDeleteConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId) {
        return;
      }

      const shouldDelete =
        typeof window === 'undefined' ? true : window.confirm(CHAT_COPY.errors.conversationDelete);
      if (!shouldDelete) {
        return;
      }

      await deleteConversation(conversationId);
    },
    [deleteConversation],
  );

  const handleExportTranscript = useCallback(() => {
    toast.info(CHAT_COPY.transcript.exportInfoTitle, {
      description: CHAT_COPY.transcript.exportInfoDescription,
    });
  }, []);

  const handleWorkspaceError = useCallback(() => {
    if (!errorMessage) {
      return;
    }
    toast.error(CHAT_COPY.errors.workspaceErrorTitle, { description: errorMessage });
    clearError();
  }, [clearError, errorMessage]);

  return {
    conversationList,
    isLoadingConversations,
    billingEvents,
    billingStreamStatus,
    agents,
    isLoadingAgents,
    agentsError,
    loadMoreConversations: loadMore,
    hasNextConversationPage: hasNextPage,
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    currentConversationId,
    selectedAgent,
    selectedAgentLabel,
    toolDrawerOpen,
    setToolDrawerOpen,
    detailDrawerOpen,
    setDetailDrawerOpen,
    isLoadingTools,
    tools,
    toolsError,
    refetchTools,
    activeAgents,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
    handleExportTranscript,
    handleWorkspaceError,
    sendMessage,
    setSelectedAgent,
  };
}
