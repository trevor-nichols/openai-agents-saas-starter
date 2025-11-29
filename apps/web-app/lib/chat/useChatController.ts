import { useCallback, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

import { deleteConversationById, fetchConversationHistory } from '@/lib/api/conversations';
import { streamChat } from '@/lib/api/chat';
import { useSendChatMutation } from '@/lib/queries/chat';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationHistory, ConversationListItem, ConversationMessage } from '@/types/conversations';
import type { ChatMessage, ConversationLifecycleStatus, RunOptionsInput, ToolState } from './types';
import type { LocationHint, MessageAttachment } from '@/lib/api/client/types.gen';

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
  activeAgent: string;
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
  runOptions?: RunOptionsInput | null;
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
  const [selectedAgent, setSelectedAgentState] = useState<string>('triage');
  const [activeAgent, setActiveAgent] = useState<string>('triage');
  const [toolEvents, setToolEvents] = useState<ToolState[]>([]);
  const [reasoningText, setReasoningText] = useState('');
  const [lifecycleStatus, setLifecycleStatus] = useState<ConversationLifecycleStatus>('idle');

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
          attachments: message.attachments ?? null,
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
      setToolEvents([]);
      setReasoningText('');
      setLifecycleStatus('idle');
      setActiveAgent(selectedAgent);

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
    [currentConversationId, mapHistoryToChatMessages, queryClient, selectedAgent],
  );

  const setSelectedAgent = useCallback((agentName: string) => {
    setSelectedAgentState(agentName);
    setActiveAgent(agentName);
  }, []);

  const startNewConversation = useCallback(() => {
    log.debug('Starting new conversation context');
    setCurrentConversationId(null);
    setMessages([]);
    setIsLoadingHistory(false);
    setErrorMessage(null);
    setToolEvents([]);
    setReasoningText('');
    setLifecycleStatus('idle');
    setActiveAgent(selectedAgent);
  }, [selectedAgent]);

  const sendMessage = useCallback(
    async (messageText: string, options?: SendMessageOptions) => {
      if (!messageText.trim() || isSending || isLoadingHistory) {
        return;
      }

      const shareLocation = options?.shareLocation ?? false;
      const locationPayload =
        shareLocation && options?.location
          ? {
              city: options.location.city?.trim() || undefined,
              region: options.location.region?.trim() || undefined,
              country: options.location.country?.trim() || undefined,
              timezone: options.location.timezone?.trim() || undefined,
            }
          : undefined;

      // Reset per-turn streaming state
      setReasoningText('');
      setToolEvents([]);
      setLifecycleStatus('idle');

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
          shareLocation,
          location: locationPayload,
          runOptions: options?.runOptions ?? undefined,
        });

        let accumulatedContent = '';
        const toolMap = new Map<string, ToolState>();
        let terminalSeen = false;
        let streamErrored = false;
        let streamedAttachments: MessageAttachment[] | null | undefined = undefined;
        let streamedStructuredOutput: unknown | null = null;
        let responseTextOverride: unknown | null = null;

        for await (const chunk of stream) {
          if (chunk.type === 'error') {
            console.error('[useChatController] Stream error:', chunk.payload);
            setErrorMessage(chunk.payload);
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `Error: ${chunk.payload}`, isStreaming: false }
                  : msg,
              ),
            );
            streamErrored = true;
            break;
          }

          const event = chunk.event;

          if (event.kind === 'agent_update' && event.new_agent) {
            setActiveAgent(event.new_agent);
          }

          if (event.kind === 'raw_response') {
            if (event.raw_type === 'response.output_text.delta' && event.text_delta) {
              accumulatedContent += event.text_delta;
              setMessages((prevMessages) =>
                prevMessages.map((msg) =>
                  msg.id === assistantMessageId
                    ? { ...msg, content: `${accumulatedContent}▋`, isStreaming: true }
                    : msg,
                ),
              );
            }

            if (
              (event.raw_type === 'response.reasoning_text.delta' ||
                event.raw_type === 'response.reasoning_summary_text.delta') &&
              event.reasoning_delta
            ) {
              setReasoningText((prev) => `${prev}${event.reasoning_delta}`);
            }

            if (event.raw_type) {
              const lifecycleMap: Record<string, ConversationLifecycleStatus> = {
                'response.created': 'created',
                'response.in_progress': 'in_progress',
                'response.completed': 'completed',
                'response.incomplete': 'incomplete',
                'response.failed': 'failed',
              };
              const nextStatus = lifecycleMap[event.raw_type];
              if (nextStatus) {
                setLifecycleStatus(nextStatus);
              }
            }

            if (event.response_text !== undefined && event.response_text !== null) {
              responseTextOverride = event.response_text;
            }
          }

          if (event.kind === 'run_item' && event.run_item_name) {
            const toolId = event.tool_call_id || event.run_item_name;
            const existing = toolMap.get(toolId) || {
              id: toolId,
              name: event.tool_name || event.run_item_name,
              status: 'input-streaming' as const,
            };

            if (event.run_item_name === 'tool_called') {
              existing.status = 'input-available';
              existing.input = event.payload;
            } else if (event.run_item_name === 'tool_output') {
              existing.status = 'output-available';
              existing.output = event.payload;
            }

            toolMap.set(toolId, existing);
            setToolEvents(Array.from(toolMap.values()));
          }

          if (event.kind === 'error') {
            const errorText =
              typeof event.payload === 'object' && event.payload && 'error' in event.payload
                ? String(event.payload.error)
                : 'Stream error';
            setErrorMessage(errorText);
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, content: `Error: ${errorText}`, isStreaming: false }
                  : msg,
              ),
            );
            streamErrored = true;
            break;
          }

          if (event.conversation_id) {
            finalConversationId = event.conversation_id;
          }

          if (event.attachments && event.attachments.length > 0) {
            streamedAttachments = event.attachments;
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, attachments: streamedAttachments ?? null }
                  : msg,
              ),
            );
          }

          if (event.structured_output !== undefined) {
            streamedStructuredOutput = event.structured_output;
            setMessages((prevMessages) =>
              prevMessages.map((msg) =>
                msg.id === assistantMessageId
                  ? { ...msg, structuredOutput: streamedStructuredOutput }
                  : msg,
              ),
            );
          }

          if (event.is_terminal) {
            terminalSeen = true;
          }

          log.debug('Processed stream event', {
            conversationId: event.conversation_id,
            accumulatedLength: accumulatedContent.length,
            kind: event.kind,
            rawType: event.raw_type,
          });

          if (event.is_terminal) {
            break;
          }
        }

        if (streamErrored) {
          return;
        }

        const finalContent = (() => {
          if (responseTextOverride !== null && responseTextOverride !== undefined) {
            if (typeof responseTextOverride === 'string') return responseTextOverride;
            try {
              return JSON.stringify(responseTextOverride);
            } catch {
              return String(responseTextOverride);
            }
          }
          return accumulatedContent;
        })();

        setMessages((prevMessages) =>
          prevMessages.map((msg) =>
            msg.id === assistantMessageId
              ? {
                  ...msg,
                  content: finalContent,
                  isStreaming: false,
                  attachments: streamedAttachments ?? msg.attachments ?? null,
                  structuredOutput: streamedStructuredOutput ?? msg.structuredOutput ?? null,
                }
              : msg,
          ),
        );

        if (terminalSeen) {
          setLifecycleStatus((prev) =>
            ['completed', 'failed', 'incomplete'].includes(prev) ? prev : 'completed'
          );
        }

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
            share_location: shareLocation,
            location: locationPayload,
            run_options: mapRunOptionsInput(options?.runOptions),
          });

          setMessages((prevMessages) =>
            prevMessages.map((msg) =>
              msg.id === assistantMessageId
                ? {
                    ...msg,
                    content: fallbackResponse.response,
                    isStreaming: false,
                    attachments: fallbackResponse.attachments ?? null,
                    structuredOutput: fallbackResponse.structured_output ?? null,
                  }
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
      activeAgent,
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
      toolEvents,
      reasoningText,
      lifecycleStatus,
    ],
  );
}

function mapRunOptionsInput(runOptions?: RunOptionsInput | null) {
  if (!runOptions) return undefined;
  let normalizedRunConfig: Record<string, unknown> | null | undefined = undefined;
  if (runOptions.runConfig === null) {
    normalizedRunConfig = null;
  } else if (typeof runOptions.runConfig === 'object') {
    normalizedRunConfig = runOptions.runConfig as Record<string, unknown>;
  }
  return {
    max_turns: runOptions.maxTurns ?? undefined,
    previous_response_id: runOptions.previousResponseId ?? undefined,
    handoff_input_filter: runOptions.handoffInputFilter ?? undefined,
    run_config: normalizedRunConfig,
  };
}
