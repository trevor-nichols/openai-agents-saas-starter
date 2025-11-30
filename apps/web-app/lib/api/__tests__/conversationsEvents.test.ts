import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

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
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
  });

  it('returns parsed events on success', async () => {
    const payload = {
      success: true,
      data: {
        conversation_id: 'conv-1',
        mode: 'transcript' as const,
        items: [],
      },
    };

    const response = new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    const result = await fetchConversationEvents({ conversationId: 'conv-1' });

    expect(result).toEqual(payload.data);
    expect(global.fetch).toHaveBeenCalledWith('/api/conversations/conv-1/events?mode=transcript', expect.any(Object));
  });

  it('throws when backend signals failure', async () => {
    const response = new Response(JSON.stringify({ success: false, error: 'oops' }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    await expect(fetchConversationEvents({ conversationId: 'conv-1' })).rejects.toThrow('oops');
  });
});

