'use server';

import type { AgentChatRequest } from '@/lib/api/client/types.gen';
import { openChatStream } from '@/lib/server/services/chat';
import type { BackendStreamData, StreamChatParams, StreamChunk } from '@/lib/chat/types';

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
    const data: BackendStreamData = JSON.parse(segment.slice(6));

    if (data.error) {
      return {
        chunk: {
          type: 'error',
          payload: data.error,
          conversationId: data.conversation_id,
        },
        done: true,
      };
    }

    return {
      chunk: {
        type: 'content',
        payload: data.chunk,
        conversationId: data.conversation_id,
      },
      done: Boolean(data.is_complete),
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
