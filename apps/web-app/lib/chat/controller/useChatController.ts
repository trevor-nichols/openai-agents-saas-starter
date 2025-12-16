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
  fetchConversationEvents,
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
import type { ConversationEvents, ConversationMessagesPage } from '@/types/conversations';
import type { LocationHint } from '@/lib/api/client/types.gen';

import { createLogger } from '@/lib/logging';
import { consumeChatStream } from '../adapters/chatStreamAdapter';
import {
  createConversationListEntry,
  dedupeAndSortMessages,
  mapMessagesToChatMessages,
  normalizeLocationPayload,
} from '../mappers/chatRequestMappers';
import {
  mapConversationEventsToToolTimeline,
  mergeToolEventAnchors,
  mergeToolStates,
  reanchorToolEventAnchors,
} from '../mappers/toolTimelineMappers';
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
  const assistantMessageIdRef = useRef<string | null>(null);
  const assistantSegmentStartOffsetRef = useRef<number>(0);
  const latestAssistantAccumulatedRef = useRef<string>('');
  const lastToolAnchorMessageIdRef = useRef<string | null>(null);
  const turnUserMessageIdRef = useRef<string | null>(null);
  const toolAnchorByIdRef = useRef<Map<string, string>>(new Map());
  const assistantIdNonceRef = useRef<number>(0);

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

  const invalidateEventsCache = useCallback(
    async (conversationId: string | null) => {
      if (!conversationId) return;
      try {
        await queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.events(conversationId),
        });
      } catch (error) {
        console.warn('[useChatController] Failed to invalidate events cache', error);
      }
    },
    [queryClient],
  );

  const messagesQueryKey = useMemo(
    () => queryKeys.conversations.messages(currentConversationId ?? 'preview'),
    [currentConversationId],
  );
  const eventsQueryKey = useMemo(
    () => queryKeys.conversations.events(currentConversationId ?? 'preview'),
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

  const { data: conversationEvents } = useQuery<ConversationEvents>({
    queryKey: eventsQueryKey,
    enabled: Boolean(currentConversationId),
    queryFn: () =>
      fetchConversationEvents({
        conversationId: currentConversationId as string,
      }),
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

  const mergedMessages = useMemo(
    () => dedupeAndSortMessages([...historyMessages, ...messages]),
    [historyMessages, messages],
  );

  const persistedToolTimeline = useMemo(() => {
    if (!conversationEvents?.items?.length) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    if (historyMessages.length === 0) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    return mapConversationEventsToToolTimeline(conversationEvents.items, historyMessages);
  }, [conversationEvents?.items, historyMessages]);

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
    assistantMessageIdRef.current = null;
    assistantSegmentStartOffsetRef.current = 0;
    latestAssistantAccumulatedRef.current = '';
    lastToolAnchorMessageIdRef.current = null;
    turnUserMessageIdRef.current = null;
    toolAnchorByIdRef.current = new Map();
  }, [selectedAgent]);

  const resetTurnState = useCallback(() => {
    setReasoningText('');
    setToolEvents([]);
    setToolEventAnchors({});
    setLifecycleStatus('idle');
    assistantMessageIdRef.current = null;
    assistantSegmentStartOffsetRef.current = 0;
    latestAssistantAccumulatedRef.current = '';
    lastToolAnchorMessageIdRef.current = null;
    turnUserMessageIdRef.current = null;
    toolAnchorByIdRef.current = new Map();
  }, []);

  const appendAgentNotice = useCallback((text: string) => {
    setAgentNotices((prev) => [...prev, { id: `agent-${Date.now()}`, text }]);
  }, []);

  const selectConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId || conversationId === currentConversationId) {
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
    [currentConversationId, resetTurnState, selectedAgent],
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
      if (!messageText.trim() || isSending) {
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

      assistantMessageIdRef.current = null;
      assistantSegmentStartOffsetRef.current = 0;
      latestAssistantAccumulatedRef.current = '';
      lastToolAnchorMessageIdRef.current = userMessage.id;
      turnUserMessageIdRef.current = userMessage.id;
      toolAnchorByIdRef.current = new Map();
      setToolEventAnchors({});

      const previousConversationId = currentConversationId;

      const ensureAssistantMessage = () => {
        if (assistantMessageIdRef.current) return assistantMessageIdRef.current;
        assistantIdNonceRef.current += 1;
        const assistantMessageId = `assistant-${Date.now()}-${assistantIdNonceRef.current}`;
        assistantMessageIdRef.current = assistantMessageId;
        enqueueMessageAction({
          type: 'append',
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
          onTextDelta: (_contentWithCursor, accumulated) => {
            latestAssistantAccumulatedRef.current = accumulated;
            const assistantMessageId = ensureAssistantMessage();
            const segmentStart = assistantSegmentStartOffsetRef.current;
            const segmentText = accumulated.slice(segmentStart);
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { content: `${segmentText}▋`, isStreaming: true },
            });
            if (segmentText.trim().length > 0) {
              // Only advance the tool anchor to the assistant message once there is real content.
              // This prevents tool calls that occur before visible assistant text from anchoring
              // to an empty cursor-only bubble.
              lastToolAnchorMessageIdRef.current = assistantMessageId;
            }
          },
          onReasoningDelta: (delta) => setReasoningText((prev) => `${prev}${delta}`),
          onToolStates: (tools) => {
            setToolEvents(tools);

            const newlySeenTools = tools.filter((tool) => !toolAnchorByIdRef.current.has(tool.id));
            if (newlySeenTools.length === 0) return;

            // Ensure any pending assistant/user message actions are committed before we anchor
            // tool cards. Without this, tool events can arrive while the assistant message is
            // still queued (requestAnimationFrame) which makes the anchor id "invisible" and
            // causes tool cards to fall into the unanchored panel (breaking chronology).
            flushQueuedMessages();

            const defaultAnchorId = lastToolAnchorMessageIdRef.current;
            const userAnchorId = turnUserMessageIdRef.current;
            const resolvedFallbackAnchorId = defaultAnchorId ?? userAnchorId;
            if (!resolvedFallbackAnchorId) return;

            const anchorAssignments = new Map<string, string[]>();
            for (const tool of newlySeenTools) {
              const shouldAnchorToUser =
                (tool.status === 'output-available' || tool.status === 'output-error') &&
                (tool.input === undefined || tool.input === null);

              const targetAnchorId =
                shouldAnchorToUser && userAnchorId ? userAnchorId : resolvedFallbackAnchorId;

              toolAnchorByIdRef.current.set(tool.id, targetAnchorId);
              const existing = anchorAssignments.get(targetAnchorId);
              if (existing) {
                existing.push(tool.id);
              } else {
                anchorAssignments.set(targetAnchorId, [tool.id]);
              }
            }

            if (anchorAssignments.size === 0) return;

            setToolEventAnchors((prev) => {
              let changed = false;
              const next: ToolEventAnchors = { ...prev };

              for (const [anchorId, toolIds] of anchorAssignments.entries()) {
                const existing = next[anchorId] ?? [];
                const deduped = new Set(existing);
                const nextIds = [...existing];

                for (const toolId of toolIds) {
                  if (!toolId || deduped.has(toolId)) continue;
                  deduped.add(toolId);
                  nextIds.push(toolId);
                  changed = true;
                }

                if (nextIds.length > existing.length) {
                  next[anchorId] = nextIds;
                }
              }

              return changed ? next : prev;
            });

            // Close the current assistant segment when a tool starts so tool cards render inline
            // between assistant message segments (ChatGPT-style).
            if (assistantMessageIdRef.current) {
              const currentAssistantId = assistantMessageIdRef.current;
              const segmentText = latestAssistantAccumulatedRef.current.slice(
                assistantSegmentStartOffsetRef.current,
              );
              if (segmentText.trim().length > 0) {
                enqueueMessageAction({
                  type: 'updateById',
                  id: currentAssistantId,
                  patch: { content: segmentText, isStreaming: false },
                });
                lastToolAnchorMessageIdRef.current = currentAssistantId;
              } else {
                // Avoid leaving a blank message bubble when tools start before the assistant
                // has produced visible content since the last segment boundary.
                enqueueMessageAction({ type: 'removeById', id: currentAssistantId });
              }
              assistantMessageIdRef.current = null;
              assistantSegmentStartOffsetRef.current = latestAssistantAccumulatedRef.current.length;
            }
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
          onAttachments: (attachments) => {
            const normalized = attachments ?? null;
            const hasAny = Array.isArray(normalized) && normalized.length > 0;
            const existingId = assistantMessageIdRef.current;
            if (!existingId && !hasAny) return;

            const assistantMessageId = existingId ?? ensureAssistantMessage();
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { attachments: normalized },
            });
          },
          onStructuredOutput: (structuredOutput) => {
            if (structuredOutput === null || structuredOutput === undefined) return;
            const assistantMessageId = ensureAssistantMessage();
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { structuredOutput },
            });
          },
          onError: (errorText) => {
            setErrorMessage(errorText);
            const assistantMessageId = ensureAssistantMessage();
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

        const finalSegmentText =
          streamResult.finalContent.length >= assistantSegmentStartOffsetRef.current
            ? streamResult.finalContent.slice(assistantSegmentStartOffsetRef.current)
            : streamResult.finalContent;

        const hasFinalText = finalSegmentText.trim().length > 0;
        const hasAttachments = (streamResult.attachments?.length ?? 0) > 0;
        const hasStructuredOutput =
          streamResult.structuredOutput !== null && streamResult.structuredOutput !== undefined;
        const hasFinalPayload =
          Boolean(assistantMessageIdRef.current) || hasFinalText || hasAttachments || hasStructuredOutput;

        if (hasFinalPayload) {
          const assistantMessageId = ensureAssistantMessage();
          enqueueMessageAction({
            type: 'updateById',
            id: assistantMessageId,
            patch: {
              content: finalSegmentText,
              isStreaming: false,
              attachments: streamResult.attachments ?? null,
              structuredOutput: streamResult.structuredOutput ?? null,
              citations: streamResult.citations ?? null,
            },
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
          void invalidateEventsCache(resolvedConversationId);
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
            const existingId = assistantMessageIdRef.current;
            if (existingId) return existingId;
            assistantIdNonceRef.current += 1;
            const nextId = `assistant-${Date.now()}-${assistantIdNonceRef.current}`;
            assistantMessageIdRef.current = nextId;
            lastToolAnchorMessageIdRef.current = nextId;
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
            void invalidateEventsCache(resolvedConversationId);
          }
        } catch (fallbackError) {
          console.error('[useChatController] Fallback send failed:', fallbackError);
          const message =
            fallbackError instanceof Error ? fallbackError.message : 'Fallback send failed.';
          setErrorMessage(message);
          log.debug('Fallback send failed', {
            error: fallbackError,
          });
          if (assistantMessageIdRef.current) {
            dispatchMessages({ type: 'removeById', id: assistantMessageIdRef.current });
          }
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
      invalidateEventsCache,
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
      clearError,
    }),
    [
      mergedMessages,
      isSending,
      isLoadingHistory,
      isClearingConversation,
      errorMessage,
      historyError,
      currentConversationId,
      selectedAgent,
      setSelectedAgent,
      sendMessage,
      selectConversation,
      startNewConversation,
      deleteConversation,
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
