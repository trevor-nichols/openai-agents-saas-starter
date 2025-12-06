import { vi } from 'vitest';

import type { ConversationListPage } from '@/types/conversations';

import { GET } from './route';

const listConversationsAction = vi.hoisted(() => vi.fn());

vi.mock('@/app/(app)/(workspace)/chat/actions', () => ({
  listConversationsAction,
}));

describe('/api/conversations route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns fetched conversations on success', async () => {
    const payload = {
      success: true,
      items: [
        { id: 'conv-1', title: 'Example', updated_at: new Date().toISOString() },
      ],
      next_cursor: null,
    };
    listConversationsAction.mockResolvedValueOnce(payload);

    const response = await GET(new Request('http://localhost/api/conversations'));

    expect(response.status).toBe(200);
    const body = (await response.json()) as ConversationListPage;
    expect(body.items).toEqual(payload.items);
    expect(body.next_cursor).toBeNull();
    expect(listConversationsAction).toHaveBeenCalledTimes(1);
  });

  it('returns 500 when the server action fails', async () => {
    const payload = {
      success: false,
      error: 'boom',
    };
    listConversationsAction.mockResolvedValueOnce(payload);

    const response = await GET(new Request('http://localhost/api/conversations'));

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ error: payload.error });
    expect(listConversationsAction).toHaveBeenCalledTimes(1);
  });
});
