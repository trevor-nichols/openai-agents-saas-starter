'use server';

import type { AgentChatRequest, StreamingChatEvent } from '@/lib/api/client/types.gen';
import { openChatStream } from '@/lib/server/services/chat';
import type { StreamChatParams, StreamChunk } from '@/lib/chat/types';

/**
 * Server-side helper to stream chat chunks directly from the backend agent service.
 * Avoids the internal /api/chat/stream hop and keeps the data path on the server.
 */
export async function* streamChatServer(
  params: StreamChatParams,
): AsyncGenerator<StreamChunk, void, unknown> {
  const payload: AgentChatRequest = {
    message: params.message,
    conversation_id: params.conversationId,
    agent_type: params.agentType ?? 'triage',
  };

  const abortController = new AbortController();

  const response = await openChatStream(payload, { signal: abortController.signal });
  if (!response.body) {
    yield { type: 'error', payload: 'No response body received' };
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const segments = buffer.split('\n\n');
      buffer = segments.pop() ?? '';

      for (const segment of segments) {
        if (!segment.trim() || !segment.startsWith('data: ')) continue;

        const result = parseBackendStream(segment);
        yield result.chunk;
        if (result.done) {
          return;
        }
      }
    }
  } finally {
    abortController.abort();
    reader.releaseLock();
  }
}

function parseBackendStream(
  segment: string,
): { chunk: StreamChunk; done: boolean } {
  try {
    const data = JSON.parse(segment.slice(6)) as unknown;

    if (typeof data === 'object' && data !== null && 'kind' in data) {
      const event = data as StreamingChatEvent;
      return {
        chunk: { type: 'event', event },
        done: Boolean(event.is_terminal),
      };
    }

    if (typeof data === 'object' && data !== null && 'error' in data) {
      const err = data as { error: string; conversation_id?: string };
      return {
        chunk: {
          type: 'error',
          payload: err.error,
          conversationId: err.conversation_id,
        },
        done: true,
      };
    }

    if (typeof data === 'object' && data !== null && 'chunk' in data) {
      const legacy = data as { chunk?: string; conversation_id?: string; is_complete?: boolean };
      const event: StreamingChatEvent = {
        kind: 'raw_response',
        conversation_id: legacy.conversation_id ?? '',
        agent_used: null,
        response_id: null,
        sequence_number: null,
        raw_type: 'response.output_text.delta',
        run_item_name: null,
        run_item_type: null,
        tool_call_id: null,
        tool_name: null,
        agent: null,
        new_agent: null,
        text_delta: legacy.chunk ?? '',
        reasoning_delta: null,
        is_terminal: Boolean(legacy.is_complete),
        payload: legacy,
      };
      return {
        chunk: { type: 'event', event },
        done: Boolean(event.is_terminal),
      };
    }

    return {
      chunk: {
        type: 'error',
        payload: 'Unknown stream payload shape',
      },
      done: true,
    };
  } catch (error) {
    return {
      chunk: {
        type: 'error',
        payload: `Failed to parse response: ${error instanceof Error ? error.message : 'Unknown error'}`,
      },
      done: true,
    };
  }
}
