import type { ChatMessage } from '../../types';
import type { MessagesAction } from '../../state/messagesReducer';

import type { TurnRuntimeRefs } from './turnRuntime';

export interface TurnMessageCoordinator {
  ensureFallbackAssistantMessage: () => string;
  ensureAssistantMessageForItem: (itemId: string, outputIndex: number) => string;
}

export interface CreateTurnMessageCoordinatorParams {
  refs: TurnRuntimeRefs;
  userMessageId: string;
  enqueueMessageAction: (action: MessagesAction) => void;
  flushQueuedMessages: () => void;
}

export function createTurnMessageCoordinator(
  params: CreateTurnMessageCoordinatorParams,
): TurnMessageCoordinator {
  const { refs, userMessageId, enqueueMessageAction, flushQueuedMessages } = params;

  const ensureFallbackAssistantMessage = () => {
    const existing = refs.lastAssistantMessageUiIdRef.current;
    if (existing) return existing;
    refs.assistantIdNonceRef.current += 1;
    const assistantMessageId = `assistant-${Date.now()}-${refs.assistantIdNonceRef.current}`;
    refs.lastAssistantMessageUiIdRef.current = assistantMessageId;
    enqueueMessageAction({
      type: 'insertAfterId',
      anchorId: userMessageId,
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
    const existing = refs.messageItemToUiIdRef.current.get(itemId);
    if (existing) return existing;

    flushQueuedMessages();

    refs.assistantIdNonceRef.current += 1;
    const uiId = `assistant-${Date.now()}-${refs.assistantIdNonceRef.current}`;
    const message: ChatMessage = {
      id: uiId,
      role: 'assistant',
      content: '▋',
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    const order = refs.assistantTurnMessagesRef.current;
    const insertAt = order.findIndex((entry) => entry.outputIndex > outputIndex);
    if (insertAt === -1) {
      const anchorId = order.length > 0 ? order[order.length - 1]?.uiId : userMessageId;
      enqueueMessageAction({
        type: 'insertAfterId',
        anchorId: anchorId ?? userMessageId,
        message,
      });
      order.push({ itemId, uiId, outputIndex });
    } else {
      const beforeId = order[insertAt]?.uiId;
      enqueueMessageAction({
        type: 'insertBeforeId',
        anchorId: beforeId ?? userMessageId,
        message,
      });
      order.splice(insertAt, 0, { itemId, uiId, outputIndex });
    }

    refs.messageItemToUiIdRef.current.set(itemId, uiId);
    refs.lastAssistantMessageUiIdRef.current = uiId;
    return uiId;
  };

  return { ensureFallbackAssistantMessage, ensureAssistantMessageForItem };
}

