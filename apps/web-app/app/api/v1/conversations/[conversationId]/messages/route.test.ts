import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ConversationMessagesPage } from '@/types/conversations';

import { GET } from './route';

const getConversationMessagesPage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  getConversationMessagesPage,
}));

const context = (conversationId?: string): Parameters<typeof GET>[1] => ({
  params: Promise.resolve({ conversationId }),
});

const request = (url = 'https://example.com/api/v1/conversations/conv-1/messages') =>
  ({ url } as unknown as NextRequest);

describe('/api/conversations/[conversationId]/messages route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns a paginated page of messages', async () => {
    const page: ConversationMessagesPage = {
      items: [],
      next_cursor: 'next-cursor',
      prev_cursor: null,
    };
    getConversationMessagesPage.mockResolvedValueOnce(page);

    const response = await GET(request(), context('conv-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(page);
    expect(getConversationMessagesPage).toHaveBeenCalledWith('conv-1', {
      cursor: undefined,
      limit: undefined,
      direction: undefined,
    });
  });

  it('returns 400 when conversation id is missing', async () => {
    const response = await GET(request(), context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation id is required.' });
    expect(getConversationMessagesPage).not.toHaveBeenCalled();
  });

  it('maps not found errors to 404', async () => {
    getConversationMessagesPage.mockRejectedValueOnce(new Error('Conversation not found'));

    const response = await GET(request(), context('missing-id'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation not found' });
  });
});
