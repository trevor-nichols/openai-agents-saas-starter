import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ConversationTitleUpdateResponse } from '@/lib/api/client/types.gen';

import { PATCH } from './route';

const updateConversationTitle = vi.hoisted(() => vi.fn());
const ConversationTitleApiError = vi.hoisted(
  () =>
    class ConversationTitleApiError extends Error {
      constructor(
        public readonly status: number,
        message: string,
      ) {
        super(message);
        this.name = 'ConversationTitleApiError';
      }
    },
);

vi.mock('@/lib/server/services/conversations', () => ({
  updateConversationTitle,
}));

vi.mock('@/lib/server/services/conversations.errors', () => ({
  ConversationTitleApiError,
}));

const context = (conversationId?: string): Parameters<typeof PATCH>[1] => ({
  params: Promise.resolve({ conversationId }),
});

const request = (body: unknown = { display_name: 'My Title' }): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(body),
    headers: new Headers({ 'x-tenant-role': 'viewer' }),
  } as unknown as NextRequest);

describe('/api/v1/conversations/[conversationId]/title route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('updates conversation title', async () => {
    const responseBody: ConversationTitleUpdateResponse = {
      conversation_id: 'conv-1',
      display_name: 'My Title',
    };
    updateConversationTitle.mockResolvedValueOnce(responseBody);

    const response = await PATCH(request(), context('conv-1'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responseBody);
    expect(updateConversationTitle).toHaveBeenCalledWith(
      'conv-1',
      { display_name: 'My Title' },
      { tenantRole: 'viewer' },
    );
  });

  it('returns 400 when conversation id is missing', async () => {
    const response = await PATCH(request(), context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation id is required.' });
    expect(updateConversationTitle).not.toHaveBeenCalled();
  });

  it('returns 422 for validation errors', async () => {
    updateConversationTitle.mockRejectedValueOnce(
      new ConversationTitleApiError(422, 'display_name must not be empty'),
    );

    const response = await PATCH(request({ display_name: '' }), context('conv-1'));

    expect(response.status).toBe(422);
    await expect(response.json()).resolves.toEqual({ message: 'display_name must not be empty' });
  });

  it('returns 404 when conversation is missing', async () => {
    updateConversationTitle.mockRejectedValueOnce(
      new ConversationTitleApiError(404, 'Conversation conv-1 does not exist'),
    );

    const response = await PATCH(request(), context('conv-1'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation conv-1 does not exist' });
  });
});
