import { describe, it, expect, vi, beforeEach, afterEach, type Mock } from 'vitest';

import { fetchConversationEvents, fetchConversationMessages } from '@/lib/api/conversations';

const originalFetch = global.fetch;

describe('fetchConversationEvents', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error cleanup mocked fetch reference
      delete global.fetch;
    }
  });

  it('returns unwrapped data when the proxy responds with success envelope', async () => {
    const payload = {
      success: true,
      data: {
        conversation_id: 'conv-123',
        items: [],
      },
    };

    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await fetchConversationEvents({ conversationId: 'conv-123' });

    expect(result).toEqual(payload.data);
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  it('throws when success is false', async () => {
    const payload = { success: false, message: 'boom' };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      fetchConversationEvents({ conversationId: 'conv-123' }),
    ).rejects.toThrow(/boom/);
  });

  it('throws when data is missing', async () => {
    const payload = { success: true };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      fetchConversationEvents({ conversationId: 'conv-123' }),
    ).rejects.toThrow(/payload was empty/i);
  });
});

describe('fetchConversationMessages', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error cleanup mocked fetch reference
      delete global.fetch;
    }
  });

  it('returns normalized pagination payload', async () => {
    const payload = {
      items: [
        { role: 'assistant', content: 'hi', timestamp: '2024-01-01T00:00:00Z' },
        { role: 'user', content: 'hello', timestamp: '2023-12-31T23:59:59Z' },
      ],
      next_cursor: 'cursor-2',
      prev_cursor: null,
    };

    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await fetchConversationMessages({ conversationId: 'conv-123', limit: 2 });

    expect(result).toEqual({ items: payload.items, next_cursor: 'cursor-2', prev_cursor: null });
    const callArg = (global.fetch as unknown as Mock).mock.calls[0]?.[0] as string;
    expect(callArg).toContain('/conversations/conv-123/messages');
    expect(callArg).toContain('limit=2');
  });

  it('throws with message from server when response not ok', async () => {
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ message: 'nope' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(
      fetchConversationMessages({ conversationId: 'conv-123', cursor: 'abc' }),
    ).rejects.toThrow(/nope/);
  });
});
