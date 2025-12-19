import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ConversationMemoryConfigResponse } from '@/lib/api/client/types.gen';

import { PATCH } from './route';

const updateConversationMemory = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  updateConversationMemory,
}));

const context = (conversationId?: string): Parameters<typeof PATCH>[1] => ({
  params: Promise.resolve({ conversationId }),
});

const request = (body: unknown = { mode: 'trim' }): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(body),
  } as unknown as NextRequest);

describe('/api/v1/conversations/[conversationId]/memory route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('updates conversation memory configuration', async () => {
    const responseBody: ConversationMemoryConfigResponse = {
      mode: 'trim',
      max_user_turns: 8,
    };
    updateConversationMemory.mockResolvedValueOnce(responseBody);

    const response = await PATCH(request(), context('conv-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responseBody);
    expect(updateConversationMemory).toHaveBeenCalledWith('conv-1', { mode: 'trim' });
  });

  it('returns 400 when conversation id is missing', async () => {
    const response = await PATCH(request(), context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation id is required.' });
    expect(updateConversationMemory).not.toHaveBeenCalled();
  });

  it('returns 422 for validation errors', async () => {
    updateConversationMemory.mockRejectedValueOnce(new Error('Validation error'));

    const response = await PATCH(request({ mode: 'invalid' }), context('conv-1'));

    expect(response.status).toBe(422);
    await expect(response.json()).resolves.toEqual({ message: 'Validation error' });
  });
});
