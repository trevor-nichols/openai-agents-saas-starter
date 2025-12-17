import { assembledText, appendDelta, replaceText, type TextParts } from '@/lib/streams/publicSseV1/textParts';

import type { ConversationLifecycleStatus, StreamChunk, Annotation } from '../../types';
import { createToolStateTracker } from './toolStateTracker';
import type { StreamConsumeResult, StreamConsumeHandlers, OutputItemUpdate } from './types';

export async function consumeChatStream(
  stream: AsyncIterable<StreamChunk>,
  handlers: StreamConsumeHandlers,
): Promise<StreamConsumeResult> {
  const messageTextByItemId = new Map<string, TextParts>();
  const refusalTextByItemId = new Map<string, TextParts>();
  let activeTextChannel: 'message' | 'refusal' = 'message';
  let lastTextItemId: string | null = null;

  let reasoningSummaryText = '';

  const toolTracker = createToolStateTracker({ onToolStates: handlers.onToolStates });

  let terminalSeen = false;
  let streamErrored = false;
  let streamedAttachments: StreamConsumeResult['attachments'] = null;
  let streamedStructuredOutput: unknown | null = null;
  let responseTextOverride: unknown | null = null;
  let lastAgent: string | null = null;
  let finalConversationId: string | null = null;
  let finalResponseId: string | null = null;
  let lifecycleStatus: ConversationLifecycleStatus = 'idle';

  const citationsByItemId = new Map<string, Annotation[]>();

  for await (const chunk of stream) {
    if (chunk.type === 'error') {
      terminalSeen = true;
      streamErrored = true;
      lifecycleStatus = 'failed';
      handlers.onError?.(chunk.payload);
      if (chunk.conversationId && finalConversationId !== chunk.conversationId) {
        finalConversationId = chunk.conversationId;
        handlers.onConversationId?.(chunk.conversationId);
      }
      break;
    }

    const event = chunk.event;
    const kind = event.kind;
    if (!kind) {
      terminalSeen = true;
      streamErrored = true;
      lifecycleStatus = 'failed';
      handlers.onError?.('Stream event missing kind');
      break;
    }

    if (event.conversation_id) {
      if (finalConversationId !== event.conversation_id) {
        finalConversationId = event.conversation_id;
        handlers.onConversationId?.(event.conversation_id);
      }
    }

    if (event.response_id) {
      finalResponseId = event.response_id;
    }

    if (event.agent && event.agent !== lastAgent) {
      lastAgent = event.agent;
      handlers.onAgentChange?.(event.agent);
    }

    if (kind === 'lifecycle') {
      lifecycleStatus = event.status;
      handlers.onLifecycle?.(lifecycleStatus);
      continue;
    }

    if (kind === 'memory.checkpoint') {
      handlers.onMemoryCheckpoint?.(event);
      continue;
    }

    if (kind === 'output_item.added' || kind === 'output_item.done') {
      const update: OutputItemUpdate = {
        itemId: event.item_id,
        outputIndex: event.output_index,
        itemType: event.item_type,
        role: event.role ?? null,
        status: event.status ?? null,
      };
      if (kind === 'output_item.added') {
        handlers.onOutputItemAdded?.(update);
        toolTracker.ensurePlaceholderForOutputItem({
          itemId: event.item_id,
          itemType: event.item_type,
          outputIndex: event.output_index,
        });
      } else {
        handlers.onOutputItemDone?.(update);
      }
      continue;
    }

    if (kind === 'message.delta') {
      const accumulated = appendDelta(messageTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      lastTextItemId = event.item_id;
      activeTextChannel = 'message';
      handlers.onTextDelta?.({
        channel: 'message',
        itemId: event.item_id,
        outputIndex: event.output_index,
        contentIndex: event.content_index,
        delta: event.delta,
        accumulatedText: accumulated,
      });
      continue;
    }

    if (kind === 'message.citation') {
      const existing = citationsByItemId.get(event.item_id) ?? [];
      citationsByItemId.set(event.item_id, [...existing, event.citation as Annotation]);
      continue;
    }

    if (kind === 'reasoning_summary.delta') {
      reasoningSummaryText += event.delta;
      handlers.onReasoningDelta?.(event.delta);
      continue;
    }

    if (kind === 'refusal.delta') {
      const accumulated = appendDelta(refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      lastTextItemId = event.item_id;
      if (activeTextChannel === 'refusal' || messageTextByItemId.size === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.({
          channel: 'refusal',
          itemId: event.item_id,
          outputIndex: event.output_index,
          contentIndex: event.content_index,
          delta: event.delta,
          accumulatedText: accumulated,
        });
      }
      continue;
    }

    if (kind === 'refusal.done') {
      const accumulated = replaceText(refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        text: event.refusal_text,
      });
      lastTextItemId = event.item_id;
      if (activeTextChannel === 'refusal' || messageTextByItemId.size === 0) {
        activeTextChannel = 'refusal';
        handlers.onTextDelta?.({
          channel: 'refusal',
          itemId: event.item_id,
          outputIndex: event.output_index,
          contentIndex: event.content_index,
          delta: '',
          accumulatedText: accumulated,
        });
      }
      continue;
    }

    if (kind === 'tool.status') {
      toolTracker.applyToolStatus(event);
      continue;
    }

    if (kind === 'tool.arguments.delta') {
      toolTracker.applyToolArgumentsDelta(event);
      continue;
    }

    if (kind === 'tool.arguments.done') {
      toolTracker.applyToolArgumentsDone(event);
      continue;
    }

    if (kind === 'tool.code.delta') {
      toolTracker.applyToolCodeDelta(event);
      continue;
    }

    if (kind === 'tool.code.done') {
      toolTracker.applyToolCodeDone(event);
      continue;
    }

    if (kind === 'tool.output') {
      toolTracker.applyToolOutput(event);
      continue;
    }

    if (kind === 'chunk.delta') {
      toolTracker.applyChunkDelta(event);
      continue;
    }

    if (kind === 'chunk.done') {
      toolTracker.applyChunkDone(event);
      continue;
    }

    if (kind === 'error') {
      terminalSeen = true;
      streamErrored = true;
      lifecycleStatus = 'failed';
      handlers.onError?.(event.error.message);
      break;
    }

    if (kind === 'final') {
      terminalSeen = true;
      lifecycleStatus = event.final.status;

      responseTextOverride =
        event.final.response_text ??
        (event.final.status === 'refused' ? event.final.refusal_text : null) ??
        null;

      streamedStructuredOutput =
        event.final.structured_output !== undefined ? event.final.structured_output : null;
      streamedAttachments = event.final.attachments ?? null;

      if (
        event.final.reasoning_summary_text &&
        event.final.reasoning_summary_text.length > reasoningSummaryText.length
      ) {
        const delta = event.final.reasoning_summary_text.slice(reasoningSummaryText.length);
        if (delta) {
          reasoningSummaryText = event.final.reasoning_summary_text;
          handlers.onReasoningDelta?.(delta);
        }
      }

      handlers.onStructuredOutput?.(streamedStructuredOutput);
      handlers.onAttachments?.(streamedAttachments);
      break;
    }
  }

  if (streamErrored) {
    return {
      finalContent: '',
      conversationId: finalConversationId,
      responseId: finalResponseId,
      attachments: streamedAttachments ?? null,
      structuredOutput: streamedStructuredOutput,
      lifecycleStatus,
      citations: null,
      terminalSeen,
      errored: true,
    };
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
    if (!lastTextItemId) return '';
    const store = activeTextChannel === 'refusal' ? refusalTextByItemId : messageTextByItemId;
    return assembledText(store.get(lastTextItemId));
  })();

  const citations = (() => {
    if (lastTextItemId && activeTextChannel === 'message') {
      const forMessage = citationsByItemId.get(lastTextItemId);
      return forMessage?.length ? forMessage : null;
    }
    const all = Array.from(citationsByItemId.values()).flat();
    return all.length ? all : null;
  })();

  if (!terminalSeen) {
    const anyRefusal = Array.from(refusalTextByItemId.values()).some(
      (parts) => assembledText(parts).length > 0,
    );
    lifecycleStatus = anyRefusal ? 'refused' : lifecycleStatus;
  }

  return {
    finalContent,
    conversationId: finalConversationId,
    responseId: finalResponseId,
    attachments: streamedAttachments ?? null,
    structuredOutput: streamedStructuredOutput ?? null,
    lifecycleStatus,
    citations,
    terminalSeen,
    errored: false,
  };
}

export type { StreamConsumeHandlers, StreamConsumeResult } from './types';
