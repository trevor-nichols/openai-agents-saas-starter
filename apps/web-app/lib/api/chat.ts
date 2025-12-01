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
  RunOptionsInput,
  StreamChunk,
  StreamChatParams,
} from '@/lib/chat/types';
import { createLogger } from '@/lib/logging';
import type { StreamingChatEvent } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

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
  const { message, conversationId, agentType = 'triage', shareLocation, location, runOptions } =
    params;

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
      run_options: mapRunOptions(runOptions),
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

        const parsed = parseStreamSegment(segment);

        if (parsed.chunk.type === 'event') {
          log.debug('Stream event', {
            kind: parsed.chunk.event.kind,
            rawType: (parsed.chunk.event as StreamingChatEvent).raw_type,
            terminal: parsed.done,
          });
        }

        if (parsed.chunk.type === 'error') {
          yield parsed.chunk;
          return;
        }

        yield parsed.chunk;

        if (parsed.done) {
          return;
        }
      }
    }
  } catch (error) {
    log.debug('Chat stream reader threw error', { error });
  } finally {
    reader.releaseLock();
  }
}

type ParsedSegment = { chunk: StreamChunk; done: boolean };

function parseStreamSegment(segment: string): ParsedSegment {
  try {
    const data = JSON.parse(segment.slice(6)) as unknown;

    // Preferred: new StreamingChatEvent shape
    if (typeof data === 'object' && data !== null && 'kind' in data) {
      const event = data as StreamingChatEvent;
      return {
        chunk: { type: 'event', event },
        done: Boolean(event.is_terminal),
      };
    }

    // Legacy error blob
    if (
      typeof data === 'object' &&
      data !== null &&
      'error' in data &&
      typeof (data as { error: unknown }).error === 'string'
    ) {
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

    // Legacy chunk-only shape: coerce into a synthetic event
    if (typeof data === 'object' && data !== null && 'chunk' in data) {
      const legacy = data as { chunk?: string; conversation_id?: string; is_complete?: boolean };
      const event: StreamingChatEvent = {
        kind: 'raw_response_event',
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
        structured_output: null,
        attachments: null,
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
    const message = error instanceof Error ? error.message : 'Unknown streaming parse error';
    log.debug('Chat stream failed to parse payload', {
      segment,
      errorMessage: message,
    });
    return {
      chunk: {
        type: 'error',
        payload: `Failed to parse stream payload: ${message}`,
      },
      done: true,
    };
  }
}

function mapRunOptions(runOptions?: RunOptionsInput) {
  if (!runOptions) return undefined;
  const { maxTurns, previousResponseId, handoffInputFilter, runConfig } = runOptions;
  return {
    max_turns: maxTurns ?? undefined,
    previous_response_id: previousResponseId ?? undefined,
    handoff_input_filter: handoffInputFilter ?? undefined,
    run_config: runConfig ?? undefined,
  };
}
