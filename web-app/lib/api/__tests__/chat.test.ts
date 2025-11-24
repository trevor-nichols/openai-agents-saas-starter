import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { AgentChatRequest } from '@/lib/api/client/types.gen';
import { sendChatMessage, streamChat } from '@/lib/api/chat';
import type { StreamChunk } from '@/lib/chat/types';

const originalFetch = global.fetch;

describe('chat API helpers', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
  });

  it('sendChatMessage returns parsed payload on success', async () => {
    const payload = {
      conversation_id: 'conv-123',
      response: 'Hello there!',
    };

    const request: AgentChatRequest = {
      message: 'Hi!',
      agent_type: 'triage',
    };

    const response = new Response(JSON.stringify(payload), {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    const result = await sendChatMessage(request);

    expect(global.fetch).toHaveBeenCalledWith('/api/chat', expect.objectContaining({
      method: 'POST',
    }));
    expect(result).toEqual(payload);
  });

  it('sendChatMessage throws ChatApiError with response details', async () => {
    const request: AgentChatRequest = {
      message: 'Hi!',
      agent_type: 'triage',
    };

    const errorPayload = {
      error: 'Something went wrong',
      code: 'chat_error',
    };

    const errorResponse = new Response(JSON.stringify(errorPayload), {
      status: 500,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(errorResponse);

    await expect(sendChatMessage(request)).rejects.toMatchObject({
      status: 500,
      message: 'Something went wrong',
      code: 'chat_error',
    });
  });

  it('streamChat yields events from SSE stream', async () => {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            'data: {"kind":"raw_response","conversation_id":"conv-1","raw_type":"response.output_text.delta","text_delta":"Hello","is_terminal":false}\n\n',
          ),
        );
        controller.enqueue(
          encoder.encode(
            'data: {"kind":"raw_response","conversation_id":"conv-1","raw_type":"response.completed","text_delta":"","is_terminal":true}\n\n',
          ),
        );
        controller.close();
      },
    });

    const response = new Response(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
      },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    const collected: StreamChunk[] = [];

    for await (const chunk of streamChat({
      message: 'Hello?',
      conversationId: null,
      agentType: 'triage',
    })) {
      collected.push(chunk);
    }

    expect(collected).toHaveLength(2);
    const first = collected[0];
    const second = collected[1];

    expect(first?.type).toBe('event');
    if (first?.type === 'event') {
      expect(first.event).toMatchObject({
        kind: 'raw_response',
        conversation_id: 'conv-1',
        text_delta: 'Hello',
      });
    }

    expect(second?.type).toBe('event');
    if (second?.type === 'event') {
      expect(second.event.is_terminal).toBe(true);
    }
  });

  it('streamChat yields error chunk when HTTP request fails', async () => {
    const response = new Response('upstream failed', {
      status: 503,
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    const chunks: StreamChunk[] = [];

    for await (const chunk of streamChat({
      message: 'Ping',
      conversationId: null,
      agentType: 'triage',
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      {
        type: 'error',
        payload: 'HTTP 503: upstream failed',
      },
    ]);
  });

  it('streamChat yields error chunk when stream body missing', async () => {
    const response = {
      ok: true,
      status: 200,
      body: null,
    } as Response;

    global.fetch = vi.fn().mockResolvedValue(response);

    const chunks: StreamChunk[] = [];

    for await (const chunk of streamChat({
      message: 'Ping',
      conversationId: null,
      agentType: 'triage',
    })) {
      chunks.push(chunk);
    }

    expect(chunks).toEqual([
      {
        type: 'error',
        payload: 'No response body received from chat stream.',
      },
    ]);
  });
});
