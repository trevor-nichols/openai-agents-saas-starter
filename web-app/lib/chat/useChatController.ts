import { useCallback, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { deleteConversationById, fetchConversationHistory } from '@/lib/api/conversations';
import { streamChat } from '@/lib/api/chat';
import { useSendChatMutation } from '@/lib/queries/chat';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationHistory, ConversationListItem, ConversationMessage } from '@/types/conversations';
import type { ChatMessage } from './types';

import { createLogger } from '@/lib/logging';

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
  sendMessage: (messageText: string) => Promise<void>;
  selectConversation: (conversationId: string) => Promise<void>;
  startNewConversation: () => void;
  deleteConversation: (conversationId: string) => Promise<void>;
  clearError: () => void;
}

export function useChatController(options: UseChatControllerOptions = {}): UseChatControllerReturn {
  const {
    onConversationAdded,
    onConversationUpdated,
    onConversationRemoved,
    reloadConversations,
  } = options;

  const sendChatMutation = useSendChatMutation();
  const queryClient = useQueryClient();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);
  const [isClearingConversation, setIsClearingConversation] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [currentConversationId, setCurrentConversationId] = useState<string | null>(null);
  const [selectedAgent, setSelectedAgent] = useState<string>('triage');

  const mapHistoryToChatMessages = useCallback((history: ConversationHistory): ChatMessage[] => {
    return history.messages
      .filter((message: ConversationMessage) => message.role !== 'system' || message.content.trim().length > 0)
      .map((message: ConversationMessage, index: number) => {
        const normalizedRole: ChatMessage['role'] = message.role === 'user' ? 'user' : 'assistant';
        const content =
          message.role === 'system' ? `[system] ${message.content}` : message.content;
        return {
          id: message.timestamp ?? `${normalizedRole}-${history.conversation_id}-${index}`,
          role: normalizedRole,
          content,
          timestamp: message.timestamp ?? undefined,
        };
      });
  }, []);

  const selectConversation = useCallback(
    async (conversationId: string) => {
      if (!conversationId || conversationId === currentConversationId) {
        return;
      }

      log.debug('Selecting conversation', { conversationId });
      setIsLoadingHistory(true);
      setMessages([]);
      setErrorMessage(null);

      try {
        const history = await queryClient.fetchQuery({
          queryKey: queryKeys.conversations.detail(conversationId),
          queryFn: () => fetchConversationHistory(conversationId),
        });
        setCurrentConversationId(history.conversation_id);
        setMessages(mapHistoryToChatMessages(history));
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
    [currentConversationId, mapHistoryToChatMessages, queryClient],
  );

  const startNewConversation = useCallback(() => {
    log.debug('Starting new conversation context');
    setCurrentConversationId(null);
    setMessages([]);
    setIsLoadingHistory(false);
    setErrorMessage(null);
  }, []);

  const sendMessage = useCallback(
    async (messageText: string) => {
      if (!messageText.trim() || isSending || isLoadingHistory) {
        return;
      }

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
      setMessages((prevMessages) => [...prevMessages, userMessage]);

      const assistantMessageId = `assistant-${Date.now()}`;
      const assistantPlaceholderMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: '▋',
        timestamp: new Date().toISOString(),
        isStreaming: true,
      };
      setMessages((prevMessages) => [...prevMessages, assistantPlaceholderMessage]);

      const previousConversationId = currentConversationId;
      let finalConversationId: string | null = null;

      try {
        const stream = streamChat({
          message: messageText,
          conversationId: previousConversationId,
          agentType: selectedAgent,
        });

        let accumulatedContent = '';

        for await (const chunk of stream) {
          if (chunk.type === 'content') {
            accumulatedContent += chunk.payload;
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `${accumulatedContent}▋`, isStreaming: true }
                  : msg,
              ),
            );

            if (chunk.conversationId) {
              finalConversationId = chunk.conversationId;
            }
            log.debug('Processed stream chunk', {
              conversationId: chunk.conversationId,
              accumulatedLength: accumulatedContent.length,
            });
          } else if (chunk.type === 'error') {
            console.error('[useChatController] Stream error:', chunk.payload);
            setErrorMessage(chunk.payload);
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `Error: ${chunk.payload}`, isStreaming: false }
                  : msg,
              ),
            );
            break;
          }
        }

        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: accumulatedContent, isStreaming: false }
              : msg,
          ),
        );

        if (finalConversationId) {
          const resolvedConversationId = finalConversationId;
          log.debug('Stream completed', {
            conversationId: resolvedConversationId,
            createdNew: !previousConversationId,
          });
          const summary =
            messageText.substring(0, 50) + (messageText.length > 50 ? '...' : '');
          const entry: ConversationListItem = {
            id: resolvedConversationId,
            last_message_summary: summary,
            updated_at: new Date().toISOString(),
          };

          if (!previousConversationId) {
            setCurrentConversationId(resolvedConversationId);
            onConversationAdded?.(entry);
          } else if (resolvedConversationId === previousConversationId) {
            onConversationUpdated?.(entry);
          }

          void queryClient
            .invalidateQueries({
              queryKey: queryKeys.conversations.detail(resolvedConversationId),
            })
            .catch((invalidateError) => {
              console.warn('[useChatController] Failed to invalidate conversation detail', invalidateError);
            });
          void queryClient
            .prefetchQuery({
              queryKey: queryKeys.conversations.detail(resolvedConversationId),
              queryFn: () => fetchConversationHistory(resolvedConversationId),
            })
            .catch((prefetchError) => {
              console.warn('[useChatController] Failed to prefetch conversation detail', prefetchError);
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
          });

          setMessages((prevMessages) =>
            prevMessages.map((msg) =>
              msg.id === assistantMessageId
                ? { ...msg, content: fallbackResponse.response, isStreaming: false }
                : msg,
            ),
          );

          const fallbackConversationId = fallbackResponse.conversation_id;
          if (fallbackConversationId) {
            const resolvedConversationId = fallbackConversationId;
            log.debug('Fallback succeeded', {
              conversationId: resolvedConversationId,
              createdNew:
                !previousConversationId || previousConversationId !== resolvedConversationId,
            });
            const summary =
              messageText.substring(0, 50) + (messageText.length > 50 ? '...' : '');
            const entry: ConversationListItem = {
              id: resolvedConversationId,
              last_message_summary: summary,
              updated_at: new Date().toISOString(),
            };

            if (!previousConversationId || previousConversationId !== resolvedConversationId) {
              setCurrentConversationId(resolvedConversationId);
              onConversationAdded?.(entry);
            } else {
              onConversationUpdated?.(entry);
            }

            void queryClient
              .invalidateQueries({
                queryKey: queryKeys.conversations.detail(resolvedConversationId),
              })
              .catch((invalidateError) => {
                console.warn('[useChatController] Failed to invalidate conversation detail', invalidateError);
              });
            void queryClient
              .prefetchQuery({
                queryKey: queryKeys.conversations.detail(resolvedConversationId),
                queryFn: () => fetchConversationHistory(resolvedConversationId),
              })
              .catch((prefetchError) => {
                console.warn('[useChatController] Failed to prefetch conversation detail', prefetchError);
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
          setMessages((prevMessages) =>
            prevMessages
              .filter((msg) => msg.id !== assistantMessageId)
              .map((msg) =>
                msg.id === userMessage.id
                  ? { ...msg, content: `${msg.content} (Error sending)` }
                  : msg,
              ),
          );
        }
      } finally {
        setIsSending(false);
      }
    },
    [
      currentConversationId,
      isLoadingHistory,
      isSending,
      onConversationAdded,
      onConversationUpdated,
      queryClient,
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
          setMessages([]);
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
      sendMessage,
      selectConversation,
      startNewConversation,
      deleteConversation,
      clearError,
    ],
  );
}
