// Server-Sent Events (SSE) streaming utilities
// Handles real-time chat streaming from the agents API

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface StreamChatParams {
  message: string;
  conversationId?: string | null;
  agentType?: string;
}

export interface StreamChunk {
  type: 'content' | 'error';
  payload: string;
  conversationId?: string;
}

interface BackendStreamData {
  chunk: string;
  conversation_id: string;
  is_complete: boolean;
  error?: string;
}

/**
 * Stream chat responses using Server-Sent Events
 * Modern, clean implementation for real-time agent communication
 */
export async function* streamChat(
  params: StreamChatParams,
): AsyncGenerator<StreamChunk, void, unknown> {
  const { message, conversationId, agentType = 'triage' } = params;

  const response = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
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
    const errorText = await response.text();
    yield {
      type: 'error',
      payload: `HTTP ${response.status}: ${errorText}`,
    };
    return;
  }

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
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (!line.trim() || !line.startsWith('data: ')) continue;

        try {
          const data: BackendStreamData = JSON.parse(line.slice(6));

          if (data.error) {
            yield {
              type: 'error',
              payload: data.error,
              conversationId: data.conversation_id,
            };
            return;
          }

          yield {
            type: 'content',
            payload: data.chunk,
            conversationId: data.conversation_id,
          };

          if (data.is_complete) return;
        } catch (error) {
          yield {
            type: 'error',
            payload: `Failed to parse response: ${error instanceof Error ? error.message : 'Unknown error'}`,
          };
          return;
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}
