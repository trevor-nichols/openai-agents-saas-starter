import type { QueryClient } from '@tanstack/react-query';

import { streamChat } from '@/lib/api/chat';
import type {
  AgentChatRequest,
  AgentChatResponse,
  AgentRunOptions,
  LocationHint,
} from '@/lib/api/client/types.gen';
import type { ConversationListItem } from '@/types/conversations';

import { consumeChatStream } from '../../adapters/chatStreamAdapter';
import { upsertConversationCaches } from '../../cache/conversationCache';
import { createConversationListEntry } from '../../mappers/chatRequestMappers';
import type { ChatMessage, ConversationLifecycleStatus, ToolEventAnchors, ToolState } from '../../types';
import type { MessagesAction } from '../../state/messagesReducer';
import { beginTurnRuntime, type TurnRuntimeRefs } from './turnRuntime';
import { computeToolEventAnchors } from './toolAnchoring';
import { createTurnMessageCoordinator } from './turnMessageCoordinator';

export interface RunChatTurnParams {
  messageText: string;
  previousConversationId: string | null;
  selectedAgent: string;
  shareLocation: boolean;
  locationPayload: Partial<LocationHint> | null;
  runOptions: AgentRunOptions | undefined;

  dispatchMessages: (action: MessagesAction) => void;
  enqueueMessageAction: (action: MessagesAction) => void;
  flushQueuedMessages: () => void;

  setErrorMessage: (message: string | null) => void;
  setToolEvents: (tools: ToolState[]) => void;
  setToolEventAnchors: (anchors: ToolEventAnchors) => void;
  setReasoningText: (updater: (prev: string) => string) => void;
  setLifecycleStatus: (status: ConversationLifecycleStatus) => void;
  setActiveAgent: (agent: string) => void;
  appendAgentNotice: (notice: string) => void;

  refs: TurnRuntimeRefs;

  queryClient: QueryClient;
  setCurrentConversationId: (conversationId: string | null) => void;
  onConversationAdded?: (conversation: ConversationListItem) => void;
  onConversationUpdated?: (conversation: ConversationListItem) => void;
  invalidateMessagesCache: (conversationId: string | null) => Promise<void>;
  invalidateLedgerCache: (conversationId: string | null) => Promise<void>;

  sendChatFallback: (payload: AgentChatRequest) => Promise<AgentChatResponse>;

  log: { debug: (message: string, fields?: Record<string, unknown>) => void };
}

const stripCursor = (content: string) => content.replace(/▋\s*$/, '');

export async function runChatTurn(params: RunChatTurnParams): Promise<void> {
  const {
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
    setLifecycleStatus,
    setActiveAgent,
    appendAgentNotice,
    refs,
    queryClient,
    setCurrentConversationId,
    onConversationAdded,
    onConversationUpdated,
    invalidateMessagesCache,
    invalidateLedgerCache,
    sendChatFallback,
    log,
  } = params;

  const userMessage: ChatMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: messageText,
    timestamp: new Date().toISOString(),
  };
  dispatchMessages({ type: 'append', message: userMessage });

  beginTurnRuntime(refs, userMessage.id);
  setToolEventAnchors({});

  const coordinator = createTurnMessageCoordinator({
    refs,
    userMessageId: userMessage.id,
    enqueueMessageAction,
    flushQueuedMessages,
  });

  const recomputeAnchors = (tools: ToolState[]) => {
    const userAnchorId = refs.turnUserMessageIdRef.current;
    if (!userAnchorId) return;
    setToolEventAnchors(
      computeToolEventAnchors({
        userAnchorId,
        assistantMessages: refs.assistantTurnMessagesRef.current,
        tools,
      }),
    );
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
          coordinator.ensureAssistantMessageForItem(update.itemId, update.outputIndex);
        }
      },
      onTextDelta: (update) => {
        const assistantMessageId = coordinator.ensureAssistantMessageForItem(
          update.itemId,
          update.outputIndex,
        );
        refs.latestAssistantTextByUiIdRef.current.set(assistantMessageId, update.accumulatedText);
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
        recomputeAnchors(tools);
      },
      onLifecycle: setLifecycleStatus,
      onAgentChange: (agent) => {
        setActiveAgent(agent);
        refs.lastActiveAgentRef.current = agent;
      },
      onAgentNotice: (notice) => {
        const current = refs.lastActiveAgentRef.current;
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
        const existingId = refs.lastAssistantMessageUiIdRef.current;
        if (!existingId && !hasAny) return;

        const assistantMessageId = existingId ?? coordinator.ensureFallbackAssistantMessage();
        enqueueMessageAction({
          type: 'updateById',
          id: assistantMessageId,
          patch: { attachments: normalized },
        });
      },
      onStructuredOutput: (structuredOutput) => {
        if (structuredOutput === null || structuredOutput === undefined) return;
        const assistantMessageId =
          refs.lastAssistantMessageUiIdRef.current ?? coordinator.ensureFallbackAssistantMessage();
        enqueueMessageAction({
          type: 'updateById',
          id: assistantMessageId,
          patch: { structuredOutput },
        });
      },
      onError: (errorText) => {
        setErrorMessage(errorText);
        const assistantMessageId =
          refs.lastAssistantMessageUiIdRef.current ?? coordinator.ensureFallbackAssistantMessage();
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
      Boolean(refs.lastAssistantMessageUiIdRef.current) ||
      hasFinalText ||
      hasAttachments ||
      hasStructuredOutput;

    if (hasFinalPayload) {
      const assistantMessageId =
        refs.lastAssistantMessageUiIdRef.current ?? coordinator.ensureFallbackAssistantMessage();
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

    const finalAssistantId = refs.lastAssistantMessageUiIdRef.current;
    for (const entry of refs.assistantTurnMessagesRef.current) {
      const latest = refs.latestAssistantTextByUiIdRef.current.get(entry.uiId) ?? '';
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
      refs.lastResponseIdRef.current = streamResult.responseId;
    }

    if (streamResult.conversationId) {
      const resolvedConversationId = streamResult.conversationId;
      log.debug('Stream completed', {
        conversationId: resolvedConversationId,
        createdNew: !previousConversationId,
      });
      const entry = createConversationListEntry(messageText, resolvedConversationId);
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
  } catch (error) {
    console.error('[runChatTurn] Streaming failed, falling back to mutation:', error);
    log.debug('Stream failed, attempting fallback', {
      error,
      previousConversationId,
    });
    try {
      const fallbackResponse = await sendChatFallback({
        message: messageText,
        conversation_id: previousConversationId ?? undefined,
        agent_type: selectedAgent,
        context: null,
        share_location: shareLocation,
        location: locationPayload,
        run_options: runOptions,
      });

      const fallbackAssistantId = (() => {
        const existingId = refs.lastAssistantMessageUiIdRef.current;
        if (existingId) return existingId;
        refs.assistantIdNonceRef.current += 1;
        const nextId = `assistant-${Date.now()}-${refs.assistantIdNonceRef.current}`;
        refs.lastAssistantMessageUiIdRef.current = nextId;
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
        refs.lastResponseIdRef.current = null;
        const resolvedConversationId = fallbackConversationId;
        log.debug('Fallback succeeded', {
          conversationId: resolvedConversationId,
          createdNew: !previousConversationId || previousConversationId !== resolvedConversationId,
        });
        const entry = createConversationListEntry(messageText, resolvedConversationId);
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
      console.error('[runChatTurn] Fallback send failed:', fallbackError);
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
  }
}

