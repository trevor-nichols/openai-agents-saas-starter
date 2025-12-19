import { vi } from 'vitest';

import type { ConversationSearchPage } from '@/types/conversations';

import { GET } from './route';

const searchConversationsPage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  searchConversationsPage,
}));

describe('/api/conversations/search route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when query is missing', async () => {
    const response = await GET(new Request('http://localhost/api/conversations/search'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ error: 'Query is required' });
    expect(searchConversationsPage).not.toHaveBeenCalled();
  });

  it('returns search results on success', async () => {
    const payload: ConversationSearchPage = {
      items: [
        { conversation_id: 'conv-1', preview: 'hello', updated_at: '2025-01-01T00:00:00.000Z', score: 0.8 },
      ],
      next_cursor: 'cursor-1',
    };
    searchConversationsPage.mockResolvedValueOnce(payload);

    const response = await GET(
      new Request('http://localhost/api/conversations/search?q=hello&limit=5&cursor=abc&agent=triage'),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(searchConversationsPage).toHaveBeenCalledWith({
      query: 'hello',
      limit: 5,
      cursor: 'abc',
      agent: 'triage',
    });
  });

  it('returns 500 when server action fails', async () => {
    searchConversationsPage.mockRejectedValueOnce(new Error('boom'));

    const response = await GET(new Request('http://localhost/api/conversations/search?q=boom'));

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ error: 'boom' });
  });
});
