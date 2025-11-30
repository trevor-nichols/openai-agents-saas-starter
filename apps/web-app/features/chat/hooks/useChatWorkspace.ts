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
    currentConversationId,
    selectedAgent,
    setSelectedAgent,
    activeAgent,
    toolEvents,
    agentNotices,
    reasoningText,
    lifecycleStatus,
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
  const [runOptions, setRunOptions] = useState({
    maxTurns: undefined as number | undefined,
    previousResponseId: '' as string | null | undefined,
    handoffInputFilter: '' as string | null | undefined,
    runConfigRaw: '' as string,
  });

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
    (message: string) => {
      const cleanedRunConfig = runOptions.runConfigRaw?.trim();
      let parsedRunConfig: unknown | null | undefined = undefined;
      if (cleanedRunConfig) {
        try {
          parsedRunConfig = JSON.parse(cleanedRunConfig);
        } catch (error) {
          toast.error('Invalid run_config JSON', {
            description: error instanceof Error ? error.message : 'Unable to parse run_config',
          });
          return Promise.resolve();
        }
      }

      return sendMessage(message, {
        shareLocation,
        location: locationHint,
        runOptions: {
          maxTurns: runOptions.maxTurns ?? null,
          previousResponseId: runOptions.previousResponseId?.trim() || null,
          handoffInputFilter: runOptions.handoffInputFilter?.trim() || null,
          runConfig: parsedRunConfig ?? null,
        },
      });
    },
    [locationHint, runOptions, sendMessage, shareLocation],
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
    activeAgent,
    agentNotices,
    toolEvents,
    reasoningText,
    lifecycleStatus,
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
    sendMessage: handleSendMessage,
    shareLocation,
    setShareLocation,
    locationHint,
    updateLocationField,
    setSelectedAgent,
    runOptions,
    setRunOptions,
    chatController,
  };
}
