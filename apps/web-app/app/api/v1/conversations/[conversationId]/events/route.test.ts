import { vi } from 'vitest';

import type { ConversationEvents } from '@/types/conversations';
import type { NextRequest } from 'next/server';

import { GET } from './route';

const getConversationEvents = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  getConversationEvents,
}));

const context = (conversationId?: string): Parameters<typeof GET>[1] => ({
  params: Promise.resolve({ conversationId }),
});

describe('/api/conversations/[conversationId]/events route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns events on success', async () => {
    const payload: ConversationEvents = {
      conversation_id: 'conv-1',
      items: [
        {
          sequence_no: 1,
          run_item_type: 'message',
          run_item_name: 'assistant',
          role: 'assistant',
          agent: 'triage',
          content_text: 'Hello',
          timestamp: new Date().toISOString(),
        },
      ],
    };

    getConversationEvents.mockResolvedValueOnce(payload);

    const response = await GET({ url: 'https://example.com/api' } as unknown as NextRequest, context('conv-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, data: payload });
    expect(getConversationEvents).toHaveBeenCalledWith('conv-1', {
      workflowRunId: undefined,
    });
  });

  it('passes workflow_run_id through to the service', async () => {
    const payload: ConversationEvents = {
      conversation_id: 'conv-1',
      items: [],
    };

    getConversationEvents.mockResolvedValueOnce(payload);

    const response = await GET(
      { url: 'https://example.com/api?workflow_run_id=run-123' } as unknown as NextRequest,
      context('conv-1'),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ success: true, data: payload });
    expect(getConversationEvents).toHaveBeenCalledWith('conv-1', {
      workflowRunId: 'run-123',
    });
  });

  it('returns 400 when conversation id missing', async () => {
    const response = await GET({ url: 'https://example.com/api' } as unknown as NextRequest, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Conversation id is required.' });
    expect(getConversationEvents).not.toHaveBeenCalled();
  });

  it('maps not found errors to 404', async () => {
    getConversationEvents.mockRejectedValueOnce(new Error('Conversation not found'));

    const response = await GET({ url: 'https://example.com/api' } as unknown as NextRequest, context('missing-id'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Conversation not found' });
  });
});
