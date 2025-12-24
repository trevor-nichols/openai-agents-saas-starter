'use client';

import { useCallback, useMemo, useState } from 'react';
import { toast } from 'sonner';

import { useChatController } from '@/lib/chat';
import { updateConversationTitle as updateConversationTitleApi } from '@/lib/api/conversations';
import type { ConversationListItem } from '@/types/conversations';
import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';
import { useTools } from '@/lib/queries/tools';

import { CHAT_COPY } from '../constants';
import { normalizeAgentLabel } from '../utils/formatters';
import { useChatWorkspacePreferences } from './useChatWorkspacePreferences';
import { useConversationTitleSync } from './useConversationTitleSync';

export function useChatWorkspace() {
  const {
    conversationList,
    isLoadingConversations,
    isFetchingMoreConversations,
    loadMore,
    hasNextPage,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
    loadConversations,
  } = useConversations();
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const chatController = useChatController({
    onConversationAdded: addConversationToList,
    onConversationUpdated: updateConversationInList,
    onConversationRemoved: removeConversationFromList,
    reloadConversations: loadConversations,
  });
  const {
    messages,
    isSending,
    isLoadingHistory,
    isClearingConversation,
    errorMessage,
    historyError,
    retryMessages,
    clearHistoryError,
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    activeAgent,
    toolEvents,
    agentNotices,
    reasoningText,
    lifecycleStatus,
    hasOlderMessages,
    isFetchingOlderMessages,
    loadOlderMessages,
    clearError,
    sendMessage,
    selectConversation,
    startNewConversation,
    deleteConversation,
  } = chatController;
  const { tools, isLoading: isLoadingTools, error: toolsError, refetch: refetchTools } = useTools();

  const [detailDrawerOpen, setDetailDrawerOpen] = useState(false);
  const [toolDrawerOpen, setToolDrawerOpen] = useState(false);
  const { shareLocation, setShareLocation, locationHint, updateLocationField } =
    useChatWorkspacePreferences();

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const selectedAgentRecord = useMemo(
    () => agents.find((agent) => agent.name === selectedAgent) ?? null,
    [agents, selectedAgent],
  );
  const selectedAgentLabel = useMemo(() => normalizeAgentLabel(selectedAgent), [selectedAgent]);
  const selectedAgentSupportsFileSearch = Boolean(
    selectedAgentRecord?.tooling?.supports_file_search,
  );
  const currentConversation = useMemo(
    () => conversationList.find((c) => c.id === currentConversationId) ?? null,
    [conversationList, currentConversationId],
  );
  const currentConversationTitle = useMemo(
    () => currentConversation?.display_name ?? currentConversation?.title ?? null,
    [currentConversation],
  );
  const titlePending = currentConversation?.display_name_pending ?? false;

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

  const getConversationBase = useCallback(
    (conversationId: string, existing?: ConversationListItem | null): ConversationListItem => {
      return (
        existing ?? {
          id: conversationId,
          updated_at: new Date().toISOString(),
          topic_hint: null,
          agent_entrypoint: null,
          active_agent: null,
          status: null,
          message_count: 0,
          last_message_preview: undefined,
        }
      );
    },
    [],
  );

  const handleRenameConversation = useCallback(
    async (conversationId: string, title: string) => {
      const normalized = (title || '').trim();
      if (!conversationId) return;
      if (!normalized) {
        throw new Error('Title cannot be empty.');
      }

      const existing = conversationList.find((c) => c.id === conversationId) ?? null;
      const base = getConversationBase(conversationId, existing);

      updateConversationInList({
        ...base,
        display_name: normalized,
        display_name_pending: false,
        title: normalized,
      });

      try {
        const updated = await updateConversationTitleApi({ conversationId, displayName: normalized });
          updateConversationInList({
            ...base,
            display_name: updated.display_name,
            display_name_pending: false,
            title: updated.display_name,
            updated_at: new Date().toISOString(),
          });
      } catch (error) {
        if (existing) {
          updateConversationInList(existing);
        }
        const message =
          error instanceof Error ? error.message : 'Failed to rename conversation title.';
        toast.error('Failed to rename conversation', { description: message });
        throw error instanceof Error ? error : new Error(message);
      }
    },
    [conversationList, getConversationBase, updateConversationInList],
  );

  useConversationTitleSync({
    conversationId: currentConversationId,
    currentConversation,
    updateConversationInList,
    getConversationBase,
  });

  const handleWorkspaceError = useCallback(() => {
    if (!errorMessage) {
      return;
    }
    toast.error(CHAT_COPY.errors.workspaceErrorTitle, { description: errorMessage });
    clearError();
  }, [clearError, errorMessage]);

  const handleSendMessage = useCallback(
    (message: string) =>
      sendMessage(message, {
        shareLocation,
        location: locationHint,
      }),
    [locationHint, sendMessage, shareLocation],
  );

  return {
    conversationList,
    isLoadingConversations,
    isFetchingMoreConversations,
    titlePending,
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
    historyError,
    retryMessages,
    clearHistoryError,
    currentConversationId,
    currentConversationTitle,
    selectedAgent,
    selectedAgentLabel,
    activeAgent,
    agentNotices,
    toolEvents,
    reasoningText,
    lifecycleStatus,
    hasOlderMessages,
    isFetchingOlderMessages,
    loadOlderMessages,
    toolDrawerOpen,
    setToolDrawerOpen,
    detailDrawerOpen,
    setDetailDrawerOpen,
    isLoadingTools,
    tools,
    toolsError,
    refetchTools,
    activeAgents,
    selectedAgentSupportsFileSearch,
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
    handleRenameConversation,
    handleWorkspaceError,
    clearError,
    sendMessage: handleSendMessage,
    shareLocation,
    setShareLocation,
    locationHint,
    updateLocationField,
    setSelectedAgent,
    chatController,
  };
}
