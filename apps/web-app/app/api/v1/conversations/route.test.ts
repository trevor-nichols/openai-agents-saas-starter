import { vi } from 'vitest';

import type { ConversationListPage } from '@/types/conversations';

import { GET } from './route';

const listConversationsPage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  listConversationsPage,
}));

describe('/api/conversations route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns fetched conversations on success', async () => {
    const payload = {
      items: [
        { id: 'conv-1', title: 'Example', updated_at: new Date().toISOString() },
      ],
      next_cursor: null,
    };
    listConversationsPage.mockResolvedValueOnce(payload);

    const response = await GET(new Request('http://localhost/api/conversations'));

    expect(response.status).toBe(200);
    const body = (await response.json()) as ConversationListPage;
    expect(body.items).toEqual(payload.items);
    expect(body.next_cursor).toBeNull();
    expect(listConversationsPage).toHaveBeenCalledTimes(1);
  });

  it('returns 500 when the server action fails', async () => {
    listConversationsPage.mockRejectedValueOnce(new Error('boom'));

    const response = await GET(new Request('http://localhost/api/conversations'));

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ error: 'boom' });
    expect(listConversationsPage).toHaveBeenCalledTimes(1);
  });
});
