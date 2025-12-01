import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { fetchConversationEvents } from '@/lib/api/conversations';

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
