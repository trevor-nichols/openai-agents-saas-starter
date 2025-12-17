import {
  useCallback,
  useMemo,
  useReducer,
  useRef,
  useState,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';

import {
  deleteConversationById,
  deleteConversationMessage,
} from '@/lib/api/conversations';
import { useSendChatMutation } from '@/lib/queries/chat';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationListItem } from '@/types/conversations';
import type {
  ChatMessage,
  ConversationLifecycleStatus,
  ToolEventAnchors,
  ToolState,
} from '../types';
import type { LocationHint, PublicSseEvent } from '@/lib/api/client/types.gen';
import type { ReasoningPart } from '@/lib/streams/publicSseV1/reasoningParts';

import { createLogger } from '@/lib/logging';
import {
  dedupeAndSortMessages,
  normalizeLocationPayload,
} from '../mappers/chatRequestMappers';
import { messagesReducer } from '../state/messagesReducer';
import { useMessageDispatchQueue } from './useMessageDispatchQueue';
import { useConversationHistory } from './useConversationHistory';
import { useToolTimeline } from './useToolTimeline';
import { runChatTurn } from './turn/runChatTurn';
import { resetTurnRuntimeRefs, resetViewRuntimeRefs, type TurnRuntimeRefs } from './turn/turnRuntime';

const log = createLogger('chat-controller');

interface ChatControllerCallbacks {
  onConversationAdded?: (conversation: ConversationListItem) => void;
  onConversationUpdated?: (conversation: ConversationListItem) => void;
  onConversationRemoved?: (conversationId: string) => void;
  reloadConversations?: () => void;
}

type UseChatControllerOptions = ChatControllerCallbacks;

export interface UseChatControllerReturn {
  messages: ChatMessage[];
  streamEvents: PublicSseEvent[];
  isSending: boolean;
  isLoadingHistory: boolean;
  isClearingConversation: boolean;
  isDeletingMessage: boolean;
  errorMessage: string | null;
  historyError: string | null;
  currentConversationId: string | null;
  selectedAgent: string;
  setSelectedAgent: (agentName: string) => void;
  activeAgent: string;
  agentNotices: AgentNotice[];
  toolEvents: ToolState[];
  toolEventAnchors: ToolEventAnchors;
  reasoningText: string;
  reasoningParts: ReasoningPart[];
  lifecycleStatus: ConversationLifecycleStatus;
  hasOlderMessages: boolean;
  isFetchingOlderMessages: boolean;
  loadOlderMessages: () => Promise<void> | void;
  retryMessages: () => void;
  clearHistoryError: () => void;
  sendMessage: (messageText: string, options?: SendMessageOptions) => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  startNewConversation: () => void;
  deleteConversation: (conversationId: string) => Promise<void>;
  deleteMessage: (messageId: string) => Promise<void>;
  clearError: () => void;
}

export interface SendMessageOptions {
  shareLocation?: boolean;
  location?: Partial<LocationHint> | null;
}

export type AgentNotice = { id: string; text: string };

export function useChatController(options: UseChatControllerOptions = {}): UseChatControllerReturn {
  const {
    onConversationAdded,
    onConversationUpdated,
    onConversationRemoved,
    reloadConversations,
  } = options;

  const sendChatMutation = useSendChatMutation();
  const queryClient = useQueryClient();

  const [messages, dispatchMessages] = useReducer(messagesReducer, []);
  const [streamEvents, setStreamEvents] = useState<PublicSseEvent[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isClearingConversation, setIsClearingConversation] = useState(false);
  const [isDeletingMessage, setIsDeletingMessage] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgentState] = useState<string>('triage');
  const [activeAgent, setActiveAgent] = useState<string>('triage');
  const [agentNotices, setAgentNotices] = useState<AgentNotice[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolState[]>([]);
  const [toolEventAnchors, setToolEventAnchors] = useState<ToolEventAnchors>({});
  const [reasoningText, setReasoningText] = useState('');
  const [reasoningParts, setReasoningParts] = useState<ReasoningPart[]>([]);
  const [lifecycleStatus, setLifecycleStatus] = useState<ConversationLifecycleStatus>('idle');
  const lastActiveAgentRef = useRef<string>('triage');
  const lastResponseIdRef = useRef<string | null>(null);
  const turnUserMessageIdRef = useRef<string | null>(null);
  const assistantIdNonceRef = useRef<number>(0);
  const messageItemToUiIdRef = useRef<Map<string, string>>(new Map());
  const assistantTurnMessagesRef = useRef<Array<{ itemId: string; uiId: string; outputIndex: number }>>([]);
  const lastAssistantMessageUiIdRef = useRef<string | null>(null);
  const latestAssistantTextByUiIdRef = useRef<Map<string, string>>(new Map());

  const turnRuntimeRefs = useMemo<TurnRuntimeRefs>(
    () => ({
      lastActiveAgentRef,
      lastResponseIdRef,
      turnUserMessageIdRef,
      assistantIdNonceRef,
      messageItemToUiIdRef,
      assistantTurnMessagesRef,
      lastAssistantMessageUiIdRef,
      latestAssistantTextByUiIdRef,
    }),
    [
      assistantIdNonceRef,
      assistantTurnMessagesRef,
      lastActiveAgentRef,
      lastAssistantMessageUiIdRef,
      lastResponseIdRef,
      latestAssistantTextByUiIdRef,
      messageItemToUiIdRef,
      turnUserMessageIdRef,
    ],
  );

  const invalidateMessagesCache = useCallback(
    async (conversationId: string | null) => {
      if (!conversationId) return;
      try {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.messages(conversationId),
        });
      } catch (error) {
        console.warn('[useChatController] Failed to invalidate messages cache', error);
      }
    },
    [queryClient],
  );

  const invalidateLedgerCache = useCallback(
    async (conversationId: string | null) => {
      if (!conversationId) return;
      try {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.ledger(conversationId),
        });
      } catch (error) {
        console.warn('[useChatController] Failed to invalidate ledger cache', error);
      }
    },
    [queryClient],
  );

  const {
    historyMessagesWithMarkers,
    ledgerEvents,
    isLoadingHistory,
    historyError,
    hasOlderMessages,
    isFetchingOlderMessages,
    loadOlderMessages,
    retryMessages,
    clearHistoryError,
  } = useConversationHistory(currentConversationId);

  const mergedMessages = useMemo(
    () => dedupeAndSortMessages([...historyMessagesWithMarkers, ...messages]),
    [historyMessagesWithMarkers, messages],
  );
  const { toolEvents: combinedToolEvents, toolEventAnchors: combinedToolEventAnchors } =
    useToolTimeline({
      ledgerEvents,
      historyMessagesWithMarkers,
      liveToolEvents: toolEvents,
      liveToolEventAnchors: toolEventAnchors,
      liveMessages: messages,
      mergedMessages,
    });

  const { enqueueMessageAction, flushQueuedMessages } = useMessageDispatchQueue(dispatchMessages);

  const resetViewState = useCallback(() => {
    dispatchMessages({ type: 'reset' });
    setStreamEvents([]);
    setErrorMessage(null);
    clearHistoryError();
    setToolEvents([]);
    setToolEventAnchors({});
    setReasoningText('');
    setReasoningParts([]);
    setAgentNotices([]);
    setLifecycleStatus('idle');
    setActiveAgent(selectedAgent);
    resetViewRuntimeRefs(turnRuntimeRefs, selectedAgent);
  }, [clearHistoryError, selectedAgent, turnRuntimeRefs]);

  const resetTurnState = useCallback(() => {
    setStreamEvents([]);
    setReasoningText('');
    setReasoningParts([]);
    setToolEvents([]);
    setToolEventAnchors({});
    setLifecycleStatus('idle');
    resetTurnRuntimeRefs(turnRuntimeRefs);
  }, [turnRuntimeRefs]);

  const appendAgentNotice = useCallback((text: string) => {
    setAgentNotices((prev) => [...prev, { id: `agent-${Date.now()}`, text }]);
  }, []);

  const appendStreamEvent = useCallback((event: PublicSseEvent) => {
    setStreamEvents((prev) => {
      const next = [...prev, event];
      // Guard: prevent unbounded growth during very long streams.
      if (next.length <= 2000) return next;
      return next.slice(next.length - 2000);
    });
  }, []);

  const selectConversation = useCallback(
    async (conversationId: string) => {
      if (
        !conversationId ||
        conversationId === currentConversationId ||
        isDeletingMessage ||
        isClearingConversation
      ) {
        return;
      }

      log.debug('Selecting conversation', { conversationId });
      dispatchMessages({ type: 'reset' });
      setErrorMessage(null);
      clearHistoryError();
      resetTurnState();
      setAgentNotices([]);
      setActiveAgent(selectedAgent);
      lastResponseIdRef.current = null;

      setCurrentConversationId(conversationId);
    },
    [
      clearHistoryError,
      currentConversationId,
      isClearingConversation,
      isDeletingMessage,
      resetTurnState,
      selectedAgent,
    ],
  );

  const setSelectedAgent = useCallback((agentName: string) => {
    setSelectedAgentState(agentName);
    setActiveAgent(agentName);
    lastActiveAgentRef.current = agentName;
  }, []);

  const startNewConversation = useCallback(() => {
    log.debug('Starting new conversation context');
    setCurrentConversationId(null);
    resetViewState();
  }, [resetViewState]);

  const sendMessage = useCallback(
    async (messageText: string, options?: SendMessageOptions) => {
      if (!messageText.trim() || isSending || isDeletingMessage || isClearingConversation) {
        return;
      }

      const shareLocation = options?.shareLocation ?? false;
      const locationPayload = normalizeLocationPayload(shareLocation, options?.location) ?? null;

      // Reset per-turn streaming state
      resetTurnState();

      setIsSending(true);
      setErrorMessage(null);
      log.debug('Sending message', {
        currentConversationId,
        length: messageText.length,
      });

      const runOptions = lastResponseIdRef.current
        ? { previous_response_id: lastResponseIdRef.current }
        : undefined;

      const previousConversationId = currentConversationId;

      try {
        await runChatTurn({
          messageText,
          previousConversationId,
          selectedAgent,
          shareLocation,
          locationPayload,
          runOptions,
          dispatchMessages,
          enqueueMessageAction,
          flushQueuedMessages,
          setErrorMessage,
          setToolEvents,
          setToolEventAnchors,
          setReasoningText,
          setReasoningParts,
          setLifecycleStatus,
          setActiveAgent,
          appendAgentNotice,
          appendStreamEvent,
          refs: turnRuntimeRefs,
          queryClient,
          setCurrentConversationId,
          onConversationAdded,
          onConversationUpdated,
          invalidateMessagesCache,
          invalidateLedgerCache,
          sendChatFallback: sendChatMutation.mutateAsync,
          log,
        });
      } finally {
        setIsSending(false);
      }
    },
    [
      currentConversationId,
      isSending,
      isClearingConversation,
      isDeletingMessage,
      appendStreamEvent,
      appendAgentNotice,
      enqueueMessageAction,
      flushQueuedMessages,
      onConversationAdded,
      onConversationUpdated,
      queryClient,
      resetTurnState,
      selectedAgent,
      sendChatMutation,
      invalidateMessagesCache,
      invalidateLedgerCache,
      setActiveAgent,
      setLifecycleStatus,
      setReasoningText,
      setReasoningParts,
      setToolEventAnchors,
      setToolEvents,
      turnRuntimeRefs,
    ],
  );

  const deleteConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId || isClearingConversation) {
        return;
      }

      log.debug('Deleting conversation', { conversationId });
      setIsClearingConversation(true);
      setErrorMessage(null);

      try {
        await deleteConversationById(conversationId);
        onConversationRemoved?.(conversationId);
        reloadConversations?.();

        queryClient.removeQueries({
          queryKey: queryKeys.conversations.detail(conversationId),
        });

        if (currentConversationId === conversationId) {
          setCurrentConversationId(null);
          dispatchMessages({ type: 'reset' });
          setAgentNotices([]);
          resetTurnState();
        }
      } catch (error) {
        console.error('[useChatController] Failed to delete conversation:', error);
        const message =
          error instanceof Error ? error.message : 'Failed to delete conversation.';
        setErrorMessage(message);
        log.debug('Delete conversation failed', { conversationId, error });
      } finally {
        setIsClearingConversation(false);
      }
    },
    [
      currentConversationId,
      isClearingConversation,
      onConversationRemoved,
      queryClient,
      resetTurnState,
      reloadConversations,
    ],
  );

  const deleteMessage = useCallback(
    async (messageId: string) => {
      const conversationId = currentConversationId;
      if (!conversationId || !messageId || isSending || isClearingConversation || isDeletingMessage) {
        return;
      }

      if (!/^[0-9]+$/.test(messageId)) {
        setErrorMessage('Only saved user messages can be deleted.');
        return;
      }

      log.debug('Deleting message', { conversationId, messageId });
      setIsDeletingMessage(true);
      setErrorMessage(null);

      try {
        await deleteConversationMessage({ conversationId, messageId });

        resetViewState();

        queryClient.removeQueries({ queryKey: queryKeys.conversations.messages(conversationId) });
        queryClient.removeQueries({ queryKey: queryKeys.conversations.ledger(conversationId) });
        queryClient.removeQueries({ queryKey: queryKeys.conversations.detail(conversationId) });

        void invalidateMessagesCache(conversationId);
        void invalidateLedgerCache(conversationId);
        void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });

        reloadConversations?.();
      } catch (error) {
        console.error('[useChatController] Failed to delete message:', error);
        const message = error instanceof Error ? error.message : 'Failed to delete message.';
        setErrorMessage(message);
        log.debug('Delete message failed', { conversationId, messageId, error });
      } finally {
        setIsDeletingMessage(false);
      }
    },
    [
      currentConversationId,
      invalidateLedgerCache,
      invalidateMessagesCache,
      isClearingConversation,
      isDeletingMessage,
      isSending,
      queryClient,
      reloadConversations,
      resetViewState,
    ],
  );

  const clearError = useCallback(() => setErrorMessage(null), []);

  return useMemo(
    () => ({
      messages: mergedMessages,
      streamEvents,
      isSending,
      isLoadingHistory,
      isClearingConversation,
      isDeletingMessage,
      errorMessage,
      historyError,
      currentConversationId,
      selectedAgent,
      setSelectedAgent,
      activeAgent,
      agentNotices,
      toolEvents: combinedToolEvents,
      toolEventAnchors: combinedToolEventAnchors,
      reasoningText,
      reasoningParts,
      lifecycleStatus,
      hasOlderMessages,
      isFetchingOlderMessages,
      loadOlderMessages,
      retryMessages,
      clearHistoryError,
      sendMessage,
      selectConversation,
      startNewConversation,
      deleteConversation,
      deleteMessage,
      clearError,
    }),
    [
      mergedMessages,
      streamEvents,
      isSending,
      isLoadingHistory,
      isClearingConversation,
      isDeletingMessage,
      errorMessage,
      historyError,
      currentConversationId,
      selectedAgent,
      setSelectedAgent,
      sendMessage,
      selectConversation,
      startNewConversation,
      deleteConversation,
      deleteMessage,
      clearError,
      activeAgent,
      agentNotices,
      combinedToolEvents,
      combinedToolEventAnchors,
      reasoningText,
      reasoningParts,
      lifecycleStatus,
      hasOlderMessages,
      isFetchingOlderMessages,
      loadOlderMessages,
      retryMessages,
      clearHistoryError,
    ],
  );

}
