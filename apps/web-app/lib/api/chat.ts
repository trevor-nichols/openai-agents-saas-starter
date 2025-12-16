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
  StreamChunk,
  StreamChatParams,
} from '@/lib/chat/types';
import { createLogger } from '@/lib/logging';
import type { StreamingChatEvent } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';
import { parseSseStream } from '@/lib/streams/sseParser';

const CHAT_ROUTE = apiV1Path('/chat');
const CHAT_STREAM_ROUTE = apiV1Path('/chat/stream');
const log = createLogger('chat-api');

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
  log.debug('Sending chat message', {
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

    log.debug('Chat message failed', {
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
    log.debug('Chat message returned empty body');
    throw new ChatApiError('Empty chat response received.', {
      status: response.status,
    });
  }

  try {
    const parsed = JSON.parse(rawBody) as AgentChatResponse;
    log.debug('Chat message succeeded', {
      conversationId: parsed.conversation_id,
    });
    return parsed;
  } catch (error) {
    log.debug('Failed to parse chat response', {
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
  const { message, conversationId, agentType = 'triage', shareLocation, location, runOptions } = params;

  log.debug('Starting chat stream', {
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
      share_location: shareLocation,
      location,
      run_options: runOptions ?? undefined,
    }),
  });

  if (!response.ok) {
    const payload = await response.text();
    log.debug('Chat stream rejected', {
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
    log.debug('Chat stream missing body');
    yield {
      type: 'error',
      payload: 'No response body received from chat stream.',
    };
    return;
  }

  let terminalSeen = false;

  try {
    for await (const evt of parseSseStream(response.body)) {
      let parsed: unknown;
      try {
        parsed = JSON.parse(evt.data) as unknown;
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Invalid JSON in stream event';
        yield {
          type: 'error',
          payload: `Failed to parse stream payload: ${message}`,
        };
        return;
      }

      if (typeof parsed !== 'object' || parsed === null || !('kind' in parsed)) {
        yield {
          type: 'error',
          payload: 'Unknown stream payload shape',
        };
        return;
      }

      const event = parsed as StreamingChatEvent;
      if (!event.kind) {
        yield {
          type: 'error',
          payload: 'Stream event missing kind',
        };
        return;
      }

      const isTerminal = event.kind === 'final' || event.kind === 'error';

      log.debug('Stream event', {
        kind: event.kind,
        terminal: isTerminal,
      });

      yield { type: 'event', event };

      if (isTerminal) {
        terminalSeen = true;
        return;
      }
    }
  } catch (error) {
    log.debug('Chat stream reader threw error', { error });
  } finally {
    // response.body is owned by parseSseStream; nothing to release here.
  }

  if (!terminalSeen) {
    yield {
      type: 'error',
      payload: 'Stream ended without a terminal event.',
    };
  }
}
