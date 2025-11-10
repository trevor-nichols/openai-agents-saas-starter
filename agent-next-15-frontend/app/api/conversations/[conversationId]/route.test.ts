import { vi } from 'vitest';

import type { ConversationHistory } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { DELETE, GET } from './route';

const getConversationHistory = vi.hoisted(() => vi.fn());
const deleteConversation = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  getConversationHistory,
  deleteConversation,
}));

const context = (conversationId?: string) =>
  ({ params: { conversationId } } as { params: { conversationId?: string } });

describe('/api/conversations/[conversationId] route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('GET', () => {
    it('returns conversation history on success', async () => {
      const payload: ConversationHistory = {
        conversation_id: 'conv-1',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        messages: [],
        agent_context: null,
      };
      getConversationHistory.mockResolvedValueOnce(payload);

      const response = await GET({} as NextRequest, context('conv-1'));

      expect(response.status).toBe(200);
      await expect(response.json()).resolves.toEqual(payload);
      expect(getConversationHistory).toHaveBeenCalledWith('conv-1');
    });

    it('returns 400 when conversation id missing', async () => {
      const response = await GET({} as NextRequest, context());

      expect(response.status).toBe(400);
      await expect(response.json()).resolves.toEqual({
        message: 'Conversation id is required.',
      });
      expect(getConversationHistory).not.toHaveBeenCalled();
    });

    it('maps not found errors to 404', async () => {
      getConversationHistory.mockRejectedValueOnce(new Error('Conversation not found'));

      const response = await GET({} as NextRequest, context('missing-id'));

      expect(response.status).toBe(404);
      await expect(response.json()).resolves.toEqual({ message: 'Conversation not found' });
    });
  });

  describe('DELETE', () => {
    it('returns 204 on success', async () => {
      deleteConversation.mockResolvedValueOnce(undefined);

      const response = await DELETE({} as NextRequest, context('conv-1'));

      expect(response.status).toBe(204);
      expect(deleteConversation).toHaveBeenCalledWith('conv-1');
    });

    it('returns 400 when conversation id missing', async () => {
      const response = await DELETE({} as NextRequest, context());

      expect(response.status).toBe(400);
      await expect(response.json()).resolves.toEqual({
        message: 'Conversation id is required.',
      });
      expect(deleteConversation).not.toHaveBeenCalled();
    });

    it('maps missing conversations to 404', async () => {
      deleteConversation.mockRejectedValueOnce(new Error('Conversation not found'));

      const response = await DELETE({} as NextRequest, context('missing-id'));

      expect(response.status).toBe(404);
      await expect(response.json()).resolves.toEqual({ message: 'Conversation not found' });
    });
  });
});

