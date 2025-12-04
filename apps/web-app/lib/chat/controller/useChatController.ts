import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type Dispatch,
} from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { deleteConversationById, fetchConversationHistory } from '@/lib/api/conversations';
import { streamChat } from '@/lib/api/chat';
import { useSendChatMutation } from '@/lib/queries/chat';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationListItem } from '@/types/conversations';
import type { ChatMessage, ConversationLifecycleStatus, ToolState } from '../types';
import type { LocationHint } from '@/lib/api/client/types.gen';

import { createLogger } from '@/lib/logging';
import { consumeChatStream } from '../adapters/chatStreamAdapter';
import {
  createConversationListEntry,
  mapHistoryToChatMessages,
  normalizeLocationPayload,
} from '../mappers/chatRequestMappers';
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
  currentConversationId: string | null;
  selectedAgent: string;
  setSelectedAgent: (agentName: string) => void;
  activeAgent: string;
  agentNotices: AgentNotice[];
  toolEvents: ToolState[];
  reasoningText: string;
  lifecycleStatus: ConversationLifecycleStatus;
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
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isClearingConversation, setIsClearingConversation] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgentState] = useState<string>('triage');
  const [activeAgent, setActiveAgent] = useState<string>('triage');
  const [agentNotices, setAgentNotices] = useState<AgentNotice[]>([]);
  const [toolEvents, setToolEvents] = useState<ToolState[]>([]);
  const [reasoningText, setReasoningText] = useState('');
  const [lifecycleStatus, setLifecycleStatus] = useState<ConversationLifecycleStatus>('idle');
  const lastActiveAgentRef = useRef<string>('triage');

      const { enqueueMessageAction, flushQueuedMessages } = useMessageDispatchQueue(dispatchMessages);

  const resetViewState = useCallback(
    () => {
      dispatchMessages({ type: 'reset' });
      setIsLoadingHistory(false);
      setErrorMessage(null);
      setToolEvents([]);
      setReasoningText('');
      setAgentNotices([]);
      setLifecycleStatus('idle');
      setActiveAgent(selectedAgent);
      lastActiveAgentRef.current = selectedAgent;
    },
    [selectedAgent],
  );

  const resetTurnState = useCallback(() => {
    setReasoningText('');
    setToolEvents([]);
    setLifecycleStatus('idle');
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
      setIsLoadingHistory(true);
      dispatchMessages({ type: 'reset' });
      setErrorMessage(null);
      resetTurnState();
      setAgentNotices([]);
      setActiveAgent(selectedAgent);

      try {
        const history = await queryClient.fetchQuery({
          queryKey: queryKeys.conversations.detail(conversationId),
          queryFn: () => fetchConversationHistory(conversationId),
        });
        setCurrentConversationId(history.conversation_id);
        dispatchMessages({ type: 'setAll', messages: mapHistoryToChatMessages(history) });
        log.debug('Conversation history loaded', {
          conversationId: history.conversation_id,
          messageCount: history.messages.length,
        });
      } catch (error) {
        console.error('[useChatController] Failed to load conversation history:', error);
        const message =
          error instanceof Error ? error.message : 'Unable to load conversation history.';
        setErrorMessage(message);
        log.debug('Conversation history failed', {
          conversationId,
          error,
        });
      } finally {
        setIsLoadingHistory(false);
      }
    },
    [currentConversationId, queryClient, resetTurnState, selectedAgent],
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
      if (!messageText.trim() || isSending || isLoadingHistory) {
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

      const userMessage: ChatMessage = {
        id: `user-${Date.now()}`,
        role: 'user',
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      dispatchMessages({ type: 'append', message: userMessage });

      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantPlaceholderMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '▋',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };
      dispatchMessages({ type: 'append', message: assistantPlaceholderMessage });

      const previousConversationId = currentConversationId;

      try {
        const stream = streamChat({
          message: messageText,
          conversationId: previousConversationId,
          agentType: selectedAgent,
          shareLocation,
          location: locationPayload,
        });

        const streamResult = await consumeChatStream(stream, {
          onTextDelta: (contentWithCursor) =>
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { content: contentWithCursor, isStreaming: true },
            }),
          onReasoningDelta: (delta) => setReasoningText((prev) => `${prev}${delta}`),
          onToolStates: setToolEvents,
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
          onAttachments: (attachments) =>
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { attachments: attachments ?? null },
            }),
          onStructuredOutput: (structuredOutput) =>
            enqueueMessageAction({
              type: 'updateById',
              id: assistantMessageId,
              patch: { structuredOutput },
            }),
          onError: (errorText) => {
            setErrorMessage(errorText);
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

        enqueueMessageAction({
          type: 'updateById',
          id: assistantMessageId,
          patch: {
            content: streamResult.finalContent,
            isStreaming: false,
            attachments: streamResult.attachments ?? null,
            structuredOutput: streamResult.structuredOutput ?? null,
            citations: streamResult.citations ?? null,
          },
        });
        flushQueuedMessages();

        setLifecycleStatus(streamResult.lifecycleStatus);

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
            // Advanced run options are disallowed server-side; omit from payload.
          });

          dispatchMessages({
            type: 'updateById',
            id: assistantMessageId,
            patch: {
              content: fallbackResponse.response,
              isStreaming: false,
              attachments: fallbackResponse.attachments ?? null,
              structuredOutput: fallbackResponse.structured_output ?? null,
            },
          });

          const fallbackConversationId = fallbackResponse.conversation_id;
          if (fallbackConversationId) {
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
          }
        } catch (fallbackError) {
          console.error('[useChatController] Fallback send failed:', fallbackError);
          const message =
            fallbackError instanceof Error ? fallbackError.message : 'Fallback send failed.';
          setErrorMessage(message);
          log.debug('Fallback send failed', {
            error: fallbackError,
          });
          dispatchMessages({ type: 'removeById', id: assistantMessageId });
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
      isLoadingHistory,
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

  return useMemo(
    () => ({
      messages,
      isSending,
      isLoadingHistory,
      isClearingConversation,
      errorMessage,
      currentConversationId,
      selectedAgent,
      setSelectedAgent,
      activeAgent,
      agentNotices,
      toolEvents,
      reasoningText,
      lifecycleStatus,
      sendMessage,
      selectConversation,
      startNewConversation,
      deleteConversation,
      clearError,
    }),
    [
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
      activeAgent,
      agentNotices,
      toolEvents,
      reasoningText,
      lifecycleStatus,
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
