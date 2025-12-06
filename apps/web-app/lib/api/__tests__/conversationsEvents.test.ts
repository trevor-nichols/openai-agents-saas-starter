import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchConversationEvents } from '@/lib/api/conversations';
import { apiV1Path } from '@/lib/apiPaths';

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
    expect(global.fetch).toHaveBeenCalledWith(apiV1Path('/conversations/conv-1/events'), expect.any(Object));
  });

  it('includes workflow_run_id when provided', async () => {
    const payload = {
      success: true,
      data: {
        conversation_id: 'conv-1',
        items: [],
      },
    };

    const response = new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    await fetchConversationEvents({ conversationId: 'conv-1', workflowRunId: 'run-42' });

    expect(global.fetch).toHaveBeenCalledWith(
      `${apiV1Path('/conversations/conv-1/events')}?workflow_run_id=run-42`,
      expect.any(Object),
    );
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
