import { vi } from 'vitest';

import type { ConversationListResponse } from '@/types/conversations';

import { GET } from './route';

const listConversationsAction = vi.hoisted(() => vi.fn());

vi.mock('../../(agent)/actions', () => ({
  listConversationsAction,
}));

describe('/api/conversations route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns fetched conversations on success', async () => {
    const payload: ConversationListResponse = {
      success: true,
      conversations: [
        {
          id: 'conv-1',
          title: 'Example',
          updated_at: new Date().toISOString(),
        },
      ],
    };
    listConversationsAction.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(listConversationsAction).toHaveBeenCalledTimes(1);
  });

  it('returns 500 when the server action fails', async () => {
    const payload: ConversationListResponse = {
      success: false,
      error: 'boom',
    };
    listConversationsAction.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual(payload);
    expect(listConversationsAction).toHaveBeenCalledTimes(1);
  });
});
