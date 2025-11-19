/**
 * Chat API helpers
 *
 * These functions are the browser-facing entry points for chat interactions.
 * They wrap Next.js API routes, provide consistent error handling, and expose
 * typed responses for downstream hooks.
 */

import type {
  AgentChatRequest,
  AgentChatResponse,
} from '@/lib/api/client/types.gen';
import type {
  BackendStreamData,
  StreamChatParams,
  StreamChunk,
} from '@/lib/chat/types';

const CHAT_ROUTE = '/api/chat';
const CHAT_STREAM_ROUTE = '/api/chat/stream';
const isProduction = typeof process !== 'undefined' && process.env.NODE_ENV === 'production';

const logDebug = (...messages: unknown[]) => {
  if (!isProduction) {
    console.debug('[chat-api]', ...messages);
  }
};

export class ChatApiError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly details?: unknown;

  constructor(message: string, options: { status: number; code?: string; details?: unknown }) {
    super(message);
    this.name = 'ChatApiError';
    this.status = options.status;
    this.code = options.code;
    this.details = options.details;
  }
}

/**
 * Send a non-streaming chat request through the proxy route.
 */
export async function sendChatMessage(payload: AgentChatRequest): Promise<AgentChatResponse> {
  logDebug('Sending chat message', {
    hasConversationId: Boolean(payload.conversation_id),
    agentType: payload.agent_type,
  });

  const response = await fetch(CHAT_ROUTE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });

  const rawBody = await response
    .clone()
    .text()
    .catch(() => '');

  if (!response.ok) {
    let parsed: Record<string, unknown> | null = null;

    try {
      parsed = rawBody ? (JSON.parse(rawBody) as Record<string, unknown>) : null;
    } catch {
      parsed = null;
    }

    const message =
      (parsed?.message as string | undefined) ??
      (parsed?.error as string | undefined) ??
      `Chat request failed (HTTP ${response.status})`;

    logDebug('Chat message failed', {
      status: response.status,
      error: message,
      details: parsed ?? undefined,
    });

    throw new ChatApiError(message, {
      status: response.status,
      code: parsed?.code as string | undefined,
      details: parsed,
    });
  }

  if (!rawBody) {
    logDebug('Chat message returned empty body');
    throw new ChatApiError('Empty chat response received.', {
      status: response.status,
    });
  }

  try {
    const parsed = JSON.parse(rawBody) as AgentChatResponse;
    logDebug('Chat message succeeded', {
      conversationId: parsed.conversation_id,
    });
    return parsed;
  } catch (error) {
    logDebug('Failed to parse chat response', {
      error,
    });
    throw new ChatApiError(
      error instanceof Error ? error.message : 'Failed to parse chat response.',
      { status: response.status },
    );
  }
}

/**
 * Stream a chat response using Server-Sent Events.
 */
export async function* streamChat(
  params: StreamChatParams,
): AsyncGenerator<StreamChunk, void, unknown> {
  const { message, conversationId, agentType = 'triage' } = params;

  logDebug('Starting chat stream', {
    agentType,
    hasConversationId: Boolean(conversationId),
  });

  const response = await fetch(CHAT_STREAM_ROUTE, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    body: JSON.stringify({
      message,
      conversation_id: conversationId,
      agent_type: agentType,
    }),
  });

  if (!response.ok) {
    const payload = await response.text();
    logDebug('Chat stream rejected', {
      status: response.status,
      payload,
    });
    yield {
      type: 'error',
      payload:
        payload.trim().length > 0
          ? `HTTP ${response.status}: ${payload}`
          : `Chat stream failed (HTTP ${response.status})`,
    };
    return;
  }

  if (!response.body) {
    logDebug('Chat stream missing body');
    yield {
      type: 'error',
      payload: 'No response body received from chat stream.',
    };
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

        try {
          const data: BackendStreamData = JSON.parse(segment.slice(6));

          if (data.error) {
            logDebug('Chat stream reported tool error', {
              conversationId: data.conversation_id,
              error: data.error,
            });
            yield {
              type: 'error',
              payload: data.error,
              conversationId: data.conversation_id,
            };
            return;
          }

          logDebug('Chat stream chunk received', {
            conversationId: data.conversation_id,
            isComplete: data.is_complete,
            chunkLength: data.chunk.length,
          });

          yield {
            type: 'content',
            payload: data.chunk,
            conversationId: data.conversation_id,
          };

          if (data.is_complete) {
            return;
          }
        } catch (error) {
          const message =
            error instanceof Error ? error.message : 'Unknown streaming parse error';
          logDebug('Chat stream failed to parse payload', {
            segment,
            errorMessage: message,
          });
          yield {
            type: 'error',
            payload: `Failed to parse stream payload: ${message}`,
          };
          return;
        }
      }
    }
  } catch (error) {
    logDebug('Chat stream reader threw error', { error });
  } finally {
    reader.releaseLock();
  }
}

