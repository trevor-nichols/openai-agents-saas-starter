import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type Dispatch,
} from 'react';
import { useInfiniteQuery, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  deleteConversationById,
  deleteConversationMessage,
  fetchConversationLedgerEvents,
  fetchConversationMessages,
} from '@/lib/api/conversations';
import { streamChat } from '@/lib/api/chat';
import { useSendChatMutation } from '@/lib/queries/chat';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationListItem } from '@/types/conversations';
import type {
  ChatMessage,
  ConversationLifecycleStatus,
  ToolEventAnchors,
  ToolState,
} from '../types';
import type { ConversationMessagesPage } from '@/types/conversations';
import type { LocationHint, PublicSseEvent } from '@/lib/api/client/types.gen';

import { createLogger } from '@/lib/logging';
import { consumeChatStream } from '../adapters/chatStreamAdapter';
import {
  createConversationListEntry,
  dedupeAndSortMessages,
  mapMessagesToChatMessages,
  normalizeLocationPayload,
} from '../mappers/chatRequestMappers';
import {
  mergeToolEventAnchors,
  mergeToolStates,
  reanchorToolEventAnchors,
} from '../mappers/toolTimelineMappers';
import {
  extractMemoryCheckpointMarkers,
  mapLedgerEventsToToolTimeline,
} from '../mappers/ledgerReplayMappers';
import { upsertConversationCaches } from '../cache/conversationCache';
import { messagesReducer, type MessagesAction } from '../state/messagesReducer';

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
  const [isSending, setIsSending] = useState(false);
  const [isClearingConversation, setIsClearingConversation] = useState(false);
  const [isDeletingMessage, setIsDeletingMessage] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgentState] = useState<string>('triage');
  const [activeAgent, setActiveAgent] = useState<string>('triage');
  const [agentNotices, setAgentNotices] = useState<AgentNotice[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolState[]>([]);
  const [toolEventAnchors, setToolEventAnchors] = useState<ToolEventAnchors>({});
  const [reasoningText, setReasoningText] = useState('');
  const [lifecycleStatus, setLifecycleStatus] = useState<ConversationLifecycleStatus>('idle');
  const lastActiveAgentRef = useRef<string>('triage');
  const lastResponseIdRef = useRef<string | null>(null);
  const turnUserMessageIdRef = useRef<string | null>(null);
  const assistantIdNonceRef = useRef<number>(0);
  const messageItemToUiIdRef = useRef<Map<string, string>>(new Map());
  const assistantTurnMessagesRef = useRef<Array<{ itemId: string; uiId: string; outputIndex: number }>>([]);
  const lastAssistantMessageUiIdRef = useRef<string | null>(null);
  const latestAssistantTextByUiIdRef = useRef<Map<string, string>>(new Map());

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

  const messagesQueryKey = useMemo(
    () => queryKeys.conversations.messages(currentConversationId ?? 'preview'),
    [currentConversationId],
  );
  const ledgerQueryKey = useMemo(
    () => queryKeys.conversations.ledger(currentConversationId ?? 'preview'),
    [currentConversationId],
  );

  const {
    data: messagesPages,
    isLoading: isLoadingMessages,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error: messagesError,
    refetch: refetchMessages,
  } = useInfiniteQuery<ConversationMessagesPage>({
    queryKey: messagesQueryKey,
    enabled: Boolean(currentConversationId),
    queryFn: ({ pageParam }) =>
      fetchConversationMessages({
        conversationId: currentConversationId as string,
        limit: 50,
        cursor: (pageParam as string | null) ?? null,
        direction: 'desc',
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as string | null,
    staleTime: 30 * 1000,
    retry: false,
  });

  const { data: ledgerEvents } = useQuery<PublicSseEvent[]>({
    queryKey: ledgerQueryKey,
    enabled: Boolean(currentConversationId),
    queryFn: () => fetchConversationLedgerEvents({ conversationId: currentConversationId as string }),
    staleTime: 30 * 1000,
    retry: false,
  });

  useEffect(() => {
    if (messagesError) {
      const message =
        messagesError instanceof Error
          ? messagesError.message
          : 'Failed to load conversation messages.';
      setHistoryError(message);
    }
  }, [messagesError, setHistoryError]);

  useEffect(() => {
    if (messagesPages) {
      setHistoryError(null);
    }
  }, [messagesPages, setHistoryError]);

  const historyMessages = useMemo(() => {
    if (!messagesPages?.pages) return [] as ChatMessage[];
    const flattened = messagesPages.pages.flatMap((page: ConversationMessagesPage) => page.items ?? []);
    return dedupeAndSortMessages(
      mapMessagesToChatMessages(flattened, currentConversationId ?? undefined),
    );
  }, [messagesPages?.pages, currentConversationId]);

  const checkpointMarkers = useMemo(
    () => (ledgerEvents?.length ? extractMemoryCheckpointMarkers(ledgerEvents) : []),
    [ledgerEvents],
  );

  const historyMessagesWithMarkers = useMemo(
    () => dedupeAndSortMessages([...historyMessages, ...checkpointMarkers]),
    [historyMessages, checkpointMarkers],
  );

  const mergedMessages = useMemo(
    () => dedupeAndSortMessages([...historyMessagesWithMarkers, ...messages]),
    [historyMessagesWithMarkers, messages],
  );

  const persistedToolTimeline = useMemo(() => {
    if (!ledgerEvents?.length) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    if (historyMessagesWithMarkers.length === 0) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    return mapLedgerEventsToToolTimeline(ledgerEvents, historyMessagesWithMarkers);
  }, [ledgerEvents, historyMessagesWithMarkers]);

  const combinedToolEvents = useMemo(
    () => mergeToolStates(persistedToolTimeline.tools, toolEvents),
    [persistedToolTimeline.tools, toolEvents],
  );

  const reanchoredToolEventAnchors = useMemo(
    () => reanchorToolEventAnchors(toolEventAnchors, messages, mergedMessages),
    [toolEventAnchors, messages, mergedMessages],
  );

  const combinedToolEventAnchors = useMemo(
    () => mergeToolEventAnchors(persistedToolTimeline.anchors, reanchoredToolEventAnchors),
    [persistedToolTimeline.anchors, reanchoredToolEventAnchors],
  );

  const isLoadingHistory = Boolean(currentConversationId) && isLoadingMessages && !messagesPages;

  const { enqueueMessageAction, flushQueuedMessages } = useMessageDispatchQueue(dispatchMessages);

  const resetViewState = useCallback(() => {
    dispatchMessages({ type: 'reset' });
    setErrorMessage(null);
    setHistoryError(null);
    setToolEvents([]);
    setToolEventAnchors({});
    setReasoningText('');
    setAgentNotices([]);
    setLifecycleStatus('idle');
    setActiveAgent(selectedAgent);
    lastActiveAgentRef.current = selectedAgent;
    lastResponseIdRef.current = null;
    turnUserMessageIdRef.current = null;
    messageItemToUiIdRef.current = new Map();
    assistantTurnMessagesRef.current = [];
    lastAssistantMessageUiIdRef.current = null;
    latestAssistantTextByUiIdRef.current = new Map();
  }, [selectedAgent]);

  const resetTurnState = useCallback(() => {
    setReasoningText('');
    setToolEvents([]);
    setToolEventAnchors({});
    setLifecycleStatus('idle');
    turnUserMessageIdRef.current = null;
    messageItemToUiIdRef.current = new Map();
    assistantTurnMessagesRef.current = [];
    lastAssistantMessageUiIdRef.current = null;
    latestAssistantTextByUiIdRef.current = new Map();
  }, []);

  const appendAgentNotice = useCallback((text: string) => {
    setAgentNotices((prev) => [...prev, { id: `agent-${Date.now()}`, text }]);
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
      setHistoryError(null);
      resetTurnState();
      setAgentNotices([]);
      setActiveAgent(selectedAgent);
      lastResponseIdRef.current = null;

      setCurrentConversationId(conversationId);
    },
    [currentConversationId, isClearingConversation, isDeletingMessage, resetTurnState, selectedAgent],
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
      const locationPayload = normalizeLocationPayload(shareLocation, options?.location);

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

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      dispatchMessages({ type: 'append', message: userMessage });

      turnUserMessageIdRef.current = userMessage.id;
      messageItemToUiIdRef.current = new Map();
      assistantTurnMessagesRef.current = [];
      lastAssistantMessageUiIdRef.current = null;
      latestAssistantTextByUiIdRef.current = new Map();
      setToolEventAnchors({});

      const previousConversationId = currentConversationId;

      const stripCursor = (content: string) => content.replace(/▋\s*$/, '');

      const ensureFallbackAssistantMessage = () => {
        const existing = lastAssistantMessageUiIdRef.current;
        if (existing) return existing;
        assistantIdNonceRef.current += 1;
        const assistantMessageId = `assistant-${Date.now()}-${assistantIdNonceRef.current}`;
        lastAssistantMessageUiIdRef.current = assistantMessageId;
        enqueueMessageAction({
          type: 'insertAfterId',
          anchorId: userMessage.id,
          message: {
            id: assistantMessageId,
            role: 'assistant',
            content: '▋',
            timestamp: new Date().toISOString(),
            isStreaming: true,
          },
        });
        return assistantMessageId;
      };

      const ensureAssistantMessageForItem = (itemId: string, outputIndex: number) => {
        const existing = messageItemToUiIdRef.current.get(itemId);
        if (existing) return existing;

        flushQueuedMessages();

        assistantIdNonceRef.current += 1;
        const uiId = `assistant-${Date.now()}-${assistantIdNonceRef.current}`;
        const message: ChatMessage = {
          id: uiId,
          role: 'assistant',
          content: '▋',
          timestamp: new Date().toISOString(),
          isStreaming: true,
        };

        const order = assistantTurnMessagesRef.current;
        const insertAt = order.findIndex((entry) => entry.outputIndex > outputIndex);
        if (insertAt === -1) {
          const anchorId = order.length > 0 ? order[order.length - 1]?.uiId : userMessage.id;
          enqueueMessageAction({
            type: 'insertAfterId',
            anchorId: anchorId ?? userMessage.id,
            message,
          });
          order.push({ itemId, uiId, outputIndex });
        } else {
          const beforeId = order[insertAt]?.uiId;
          enqueueMessageAction({
            type: 'insertBeforeId',
            anchorId: beforeId ?? userMessage.id,
            message,
          });
          order.splice(insertAt, 0, { itemId, uiId, outputIndex });
        }

        messageItemToUiIdRef.current.set(itemId, uiId);
        lastAssistantMessageUiIdRef.current = uiId;
        return uiId;
      };

      const recomputeToolAnchors = (tools: ToolState[]) => {
        const userAnchorId = turnUserMessageIdRef.current;
        if (!userAnchorId) return;

        const messageOrder = [...assistantTurnMessagesRef.current].sort(
          (a, b) => a.outputIndex - b.outputIndex,
        );
        const sortedTools = [...tools].sort(
          (a, b) =>
            (a.outputIndex ?? Number.POSITIVE_INFINITY) -
            (b.outputIndex ?? Number.POSITIVE_INFINITY),
        );

        const nextAnchors: ToolEventAnchors = {};
        for (const tool of sortedTools) {
          const toolIndex = tool.outputIndex ?? Number.POSITIVE_INFINITY;
          let anchorId = userAnchorId;
          for (const msg of messageOrder) {
            if (msg.outputIndex < toolIndex) {
              anchorId = msg.uiId;
            } else {
              break;
            }
          }
          const ids = nextAnchors[anchorId];
          if (ids) ids.push(tool.id);
          else nextAnchors[anchorId] = [tool.id];
        }

        setToolEventAnchors(nextAnchors);
      };

      try {
        const stream = streamChat({
          message: messageText,
          conversationId: previousConversationId,
          agentType: selectedAgent,
          shareLocation,
          location: locationPayload,
          runOptions,
        });

        const streamResult = await consumeChatStream(stream, {
          onOutputItemAdded: (update) => {
            if (update.itemType === 'message' && update.role === 'assistant') {
              ensureAssistantMessageForItem(update.itemId, update.outputIndex);
            }
          },
          onTextDelta: (update) => {
            const assistantMessageId = ensureAssistantMessageForItem(update.itemId, update.outputIndex);
            latestAssistantTextByUiIdRef.current.set(assistantMessageId, update.accumulatedText);
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { content: update.textWithCursor, isStreaming: true },
            });
          },
          onReasoningDelta: (delta) => setReasoningText((prev) => `${prev}${delta}`),
          onToolStates: (tools) => {
            setToolEvents(tools);
            flushQueuedMessages();
            recomputeToolAnchors(tools);
          },
          onLifecycle: setLifecycleStatus,
          onAgentChange: (agent) => {
            setActiveAgent(agent);
            lastActiveAgentRef.current = agent;
          },
          onAgentNotice: (notice) => {
            const current = lastActiveAgentRef.current;
            if (notice.endsWith(current)) return;
            appendAgentNotice(notice);
          },
          onMemoryCheckpoint: (checkpointEvent) => {
            enqueueMessageAction({
              type: 'append',
              message: {
                id: `memory-checkpoint-${checkpointEvent.stream_id}-${checkpointEvent.event_id}`,
                role: 'assistant',
                kind: 'memory_checkpoint',
                content: '',
                timestamp: checkpointEvent.server_timestamp,
                checkpoint: checkpointEvent.checkpoint,
              },
            });
            flushQueuedMessages();
          },
          onAttachments: (attachments) => {
            const normalized = attachments ?? null;
            const hasAny = Array.isArray(normalized) && normalized.length > 0;
            const existingId = lastAssistantMessageUiIdRef.current;
            if (!existingId && !hasAny) return;

            const assistantMessageId = existingId ?? ensureFallbackAssistantMessage();
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { attachments: normalized },
            });
          },
          onStructuredOutput: (structuredOutput) => {
            if (structuredOutput === null || structuredOutput === undefined) return;
            const assistantMessageId = lastAssistantMessageUiIdRef.current ?? ensureFallbackAssistantMessage();
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { structuredOutput },
            });
          },
          onError: (errorText) => {
            setErrorMessage(errorText);
            const assistantMessageId = lastAssistantMessageUiIdRef.current ?? ensureFallbackAssistantMessage();
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { content: `Error: ${errorText}`, isStreaming: false },
            });
          },
        });

        if (streamResult.errored) {
          flushQueuedMessages();
          return;
        }

        const finalText = stripCursor(streamResult.finalContent);
        const hasFinalText = finalText.trim().length > 0;
        const hasAttachments = (streamResult.attachments?.length ?? 0) > 0;
        const hasStructuredOutput =
          streamResult.structuredOutput !== null && streamResult.structuredOutput !== undefined;
        const hasFinalPayload =
          Boolean(lastAssistantMessageUiIdRef.current) || hasFinalText || hasAttachments || hasStructuredOutput;

        if (hasFinalPayload) {
          const assistantMessageId = lastAssistantMessageUiIdRef.current ?? ensureFallbackAssistantMessage();
          enqueueMessageAction({
            type: 'updateById',
            id: assistantMessageId,
            patch: {
              content: finalText,
              isStreaming: false,
              attachments: streamResult.attachments ?? null,
              structuredOutput: streamResult.structuredOutput ?? null,
              citations: streamResult.citations ?? null,
            },
          });
        }

        const finalAssistantId = lastAssistantMessageUiIdRef.current;
        for (const entry of assistantTurnMessagesRef.current) {
          const latest = latestAssistantTextByUiIdRef.current.get(entry.uiId) ?? '';
          const content =
            entry.uiId === finalAssistantId && hasFinalPayload ? finalText : stripCursor(latest);
          const patch: Partial<ChatMessage> = { isStreaming: false };
          if (content) patch.content = content;
          enqueueMessageAction({
            type: 'updateById',
            id: entry.uiId,
            patch,
          });
        }
        flushQueuedMessages();

        setLifecycleStatus(streamResult.lifecycleStatus);

        if (streamResult.responseId) {
          lastResponseIdRef.current = streamResult.responseId;
        }

        if (streamResult.conversationId) {
          const resolvedConversationId = streamResult.conversationId;
          log.debug('Stream completed', {
            conversationId: resolvedConversationId,
            createdNew: !previousConversationId,
          });
          const entry = createConversationListEntry(messageText, resolvedConversationId);
          // Fire-and-forget cache refresh to keep composer responsive
          void upsertConversationCaches({
            queryClient,
            resolvedConversationId,
            previousConversationId,
            entry,
            setCurrentConversationId,
            onConversationAdded,
            onConversationUpdated,
          });
          // Ensure paginated messages refresh picks up the new turn
          void invalidateMessagesCache(resolvedConversationId);
          void invalidateLedgerCache(resolvedConversationId);
        }
      } catch (error) {
        console.error('[useChatController] Streaming failed, falling back to mutation:', error);
        log.debug('Stream failed, attempting fallback', {
          error,
          previousConversationId,
        });
        try {
          const fallbackResponse = await sendChatMutation.mutateAsync({
            message: messageText,
            conversation_id: previousConversationId ?? undefined,
            agent_type: selectedAgent,
            context: null,
            share_location: shareLocation,
            location: locationPayload,
            run_options: runOptions,
          });

          const fallbackAssistantId = (() => {
            const existingId = lastAssistantMessageUiIdRef.current;
            if (existingId) return existingId;
            assistantIdNonceRef.current += 1;
            const nextId = `assistant-${Date.now()}-${assistantIdNonceRef.current}`;
            lastAssistantMessageUiIdRef.current = nextId;
            dispatchMessages({
              type: 'append',
              message: {
                id: nextId,
                role: 'assistant',
                content: fallbackResponse.response,
                timestamp: new Date().toISOString(),
                isStreaming: false,
                attachments: fallbackResponse.attachments ?? null,
                structuredOutput: fallbackResponse.structured_output ?? null,
              },
            });
            return nextId;
          })();

          dispatchMessages({
            type: 'updateById',
            id: fallbackAssistantId,
            patch: {
              content: fallbackResponse.response,
              isStreaming: false,
              attachments: fallbackResponse.attachments ?? null,
              structuredOutput: fallbackResponse.structured_output ?? null,
            },
          });

          const fallbackConversationId = fallbackResponse.conversation_id;
          if (fallbackConversationId) {
            lastResponseIdRef.current = null;
            const resolvedConversationId = fallbackConversationId;
            log.debug('Fallback succeeded', {
              conversationId: resolvedConversationId,
              createdNew:
                !previousConversationId || previousConversationId !== resolvedConversationId,
            });
            const entry = createConversationListEntry(messageText, resolvedConversationId);
            // Fire-and-forget cache refresh to keep composer responsive
            void upsertConversationCaches({
              queryClient,
              resolvedConversationId,
              previousConversationId,
              entry,
              setCurrentConversationId,
              onConversationAdded,
              onConversationUpdated,
            });
            void invalidateMessagesCache(resolvedConversationId);
            void invalidateLedgerCache(resolvedConversationId);
          }
        } catch (fallbackError) {
          console.error('[useChatController] Fallback send failed:', fallbackError);
          const message =
            fallbackError instanceof Error ? fallbackError.message : 'Fallback send failed.';
          setErrorMessage(message);
          log.debug('Fallback send failed', {
            error: fallbackError,
          });
          dispatchMessages({
            type: 'updateById',
            id: userMessage.id,
            patch: { content: `${userMessage.content} (Error sending)` },
          });
        }
      } finally {
        setIsSending(false);
      }
    },
    [
      currentConversationId,
      isSending,
      isClearingConversation,
      isDeletingMessage,
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
  const clearHistoryError = useCallback(() => setHistoryError(null), []);

  const loadOlderMessages = useCallback(async () => {
    if (!hasNextPage) return;
    try {
      await fetchNextPage();
    } catch (error) {
      console.error('[useChatController] Failed to load older messages:', error);
      setHistoryError(
        error instanceof Error ? error.message : 'Failed to load older messages.',
      );
    }
  }, [fetchNextPage, hasNextPage]);

  const retryMessages = useCallback(() => {
    setHistoryError(null);
    void refetchMessages();
  }, [refetchMessages]);

  return useMemo(
    () => ({
      messages: mergedMessages,
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
      lifecycleStatus,
      hasOlderMessages: Boolean(hasNextPage),
      isFetchingOlderMessages: isFetchingNextPage,
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
      lifecycleStatus,
      hasNextPage,
      isFetchingNextPage,
      loadOlderMessages,
      retryMessages,
      clearHistoryError,
    ],
  );

}

function useMessageDispatchQueue(dispatch: Dispatch<MessagesAction>) {
  const queueRef = useRef<MessagesAction[]>([]);
  const frameRef = useRef<number | null>(null);

  const flushQueuedMessages = useCallback(() => {
    if (!queueRef.current.length) {
      frameRef.current = null;
      return;
    }
    dispatch({ type: 'batch', actions: queueRef.current });
    queueRef.current = [];
    frameRef.current = null;
  }, [dispatch]);

  const enqueueMessageAction = useCallback(
    (action: MessagesAction) => {
      queueRef.current.push(action);
      if (frameRef.current === null) {
        frameRef.current = requestAnimationFrame(flushQueuedMessages);
      }
    },
    [flushQueuedMessages],
  );

  useEffect(() => {
    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
      queueRef.current = [];
    };
  }, []);

  return { enqueueMessageAction, flushQueuedMessages };
}
