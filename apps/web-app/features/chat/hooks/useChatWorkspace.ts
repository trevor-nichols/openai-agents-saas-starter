'use client';

import { useCallback, useMemo, useState, useEffect } from 'react';
import { toast } from 'sonner';

import { useChatController } from '@/lib/chat';
import type { LocationHint } from '@/lib/api/client/types.gen';
import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';
import { useTools } from '@/lib/queries/tools';

import { CHAT_COPY } from '../constants';
import { normalizeAgentLabel } from '../utils/formatters';
import { useConversationTitleStream } from './useConversationTitleStream';

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
    guardrailEvents,
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
  const [shareLocation, setShareLocation] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    try {
      const stored = window.localStorage.getItem('chat.shareLocation');
      if (stored !== null) {
        return stored === 'true';
      }
    } catch {
      /* ignore */
    }
    return false;
  });
  const [locationHint, setLocationHint] = useState<Partial<LocationHint>>(() => {
    const fallback = { timezone: Intl?.DateTimeFormat?.().resolvedOptions().timeZone };
    if (typeof window === 'undefined') return fallback;
    try {
      const stored = window.localStorage.getItem('chat.locationHint');
      if (stored) {
        const parsed = JSON.parse(stored) as Partial<LocationHint>;
        return { ...fallback, ...parsed };
      }
    } catch {
      /* ignore */
    }
    return fallback;
  });

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const selectedAgentLabel = useMemo(() => normalizeAgentLabel(selectedAgent), [selectedAgent]);
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

  const setPending = useCallback(
    (pending: boolean) => {
      if (!currentConversationId) return;
      const base = currentConversation ?? {
        id: currentConversationId,
        updated_at: new Date().toISOString(),
        topic_hint: null,
        agent_entrypoint: null,
        active_agent: null,
        status: null,
        message_count: 0,
        last_message_preview: undefined,
      };
      updateConversationInList({
        ...base,
        display_name_pending: pending,
      });
    },
    [currentConversation, currentConversationId, updateConversationInList],
  );

  const handleTitle = useCallback(
    (title: string) => {
      if (!currentConversationId) return;
      const base = currentConversation ?? {
        id: currentConversationId,
        updated_at: new Date().toISOString(),
        topic_hint: null,
        agent_entrypoint: null,
        active_agent: null,
        status: null,
        message_count: 0,
        last_message_preview: undefined,
      };
      updateConversationInList({
        ...base,
        display_name: title,
        title,
      });
    },
    [currentConversation, currentConversationId, updateConversationInList],
  );

  useConversationTitleStream({
    conversationId: currentConversationId,
    onTitle: handleTitle,
    onPendingStart: () => setPending(true),
    onPendingResolve: () => setPending(false),
  });

  const handleWorkspaceError = useCallback(() => {
    if (!errorMessage) {
      return;
    }
    toast.error(CHAT_COPY.errors.workspaceErrorTitle, { description: errorMessage });
    clearError();
  }, [clearError, errorMessage]);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      window.localStorage.setItem('chat.shareLocation', String(shareLocation));
      window.localStorage.setItem('chat.locationHint', JSON.stringify(locationHint));
    } catch {
      // ignore storage errors
    }
  }, [shareLocation, locationHint]);

  const handleSendMessage = useCallback(
    (message: string) =>
      sendMessage(message, {
        shareLocation,
        location: locationHint,
      }),
    [locationHint, sendMessage, shareLocation],
  );

  const updateLocationField = useCallback(
    (field: keyof LocationHint, value: string) =>
      setLocationHint((prev) => ({
        ...prev,
        [field]: value,
      })),
    [],
  );

  return {
    conversationList,
    isLoadingConversations,
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
    guardrailEvents,
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
    handleSelectConversation,
    handleNewConversation,
    handleDeleteConversation,
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
