import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ConversationMessageDeleteResponse } from '@/lib/api/client/types.gen';

import { DELETE } from './route';

const deleteConversationMessage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  deleteConversationMessage,
}));

const context = (conversationId?: string, messageId?: string): Parameters<typeof DELETE>[1] => ({
  params: Promise.resolve({ conversationId, messageId }),
});

const request = (url = 'https://example.com/api/v1/conversations/conv-1/messages/123') =>
  ({ url } as unknown as NextRequest);

describe('/api/conversations/[conversationId]/messages/[messageId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('deletes a message and returns the deletion response', async () => {
    const payload: ConversationMessageDeleteResponse = {
      conversation_id: 'conv-1',
      deleted_message_id: '123',
    };
    deleteConversationMessage.mockResolvedValueOnce(payload);

    const response = await DELETE(request(), context('conv-1', '123'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(deleteConversationMessage).toHaveBeenCalledWith({ conversationId: 'conv-1', messageId: '123' });
  });

  it('returns 400 when conversation id is missing', async () => {
    const response = await DELETE(request(), context(undefined, '123'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Conversation id is required.' });
    expect(deleteConversationMessage).not.toHaveBeenCalled();
  });

  it('returns 400 when message id is missing', async () => {
    const response = await DELETE(request(), context('conv-1', undefined));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Message id is required.' });
    expect(deleteConversationMessage).not.toHaveBeenCalled();
  });

  it('maps not found errors to 404', async () => {
    deleteConversationMessage.mockRejectedValueOnce(new Error('Message not found'));

    const response = await DELETE(request(), context('conv-1', '999'));

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Message not found' });
  });
});

