import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { getConversationMessagesPage } from '../conversations';

const getServerApiClient = vi.hoisted(() => vi.fn());
const getConversationMessagesApiV1ConversationsConversationIdMessagesGet = vi.hoisted(() => vi.fn());

vi.mock('../../apiClient', () => ({
  getServerApiClient,
}));

vi.mock('@/lib/api/client/sdk.gen', () => ({
  getConversationMessagesApiV1ConversationsConversationIdMessagesGet,
}));

describe('getConversationMessagesPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('returns normalized messages and cursors', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    getConversationMessagesApiV1ConversationsConversationIdMessagesGet.mockResolvedValue({
      data: {
        items: [{ role: 'assistant', content: 'hi', timestamp: '2024-01-01T00:00:00Z' }],
        next_cursor: 'next-cursor',
        prev_cursor: null,
      },
    });

    const result = await getConversationMessagesPage('conv-1', {
      cursor: 'cursor-1',
      limit: 25,
      direction: 'desc',
    });

    expect(getConversationMessagesApiV1ConversationsConversationIdMessagesGet).toHaveBeenCalledWith({
      client: 'client',
      auth: 'auth',
      responseStyle: 'fields',
      throwOnError: true,
      path: { conversation_id: 'conv-1' },
      query: { cursor: 'cursor-1', limit: 25, direction: 'desc' },
    });

    expect(result).toEqual({
      items: [{ role: 'assistant', content: 'hi', timestamp: '2024-01-01T00:00:00Z' }],
      next_cursor: 'next-cursor',
      prev_cursor: null,
    });
  });

  it('returns empty defaults when payload missing', async () => {
    getServerApiClient.mockResolvedValue({ client: 'client', auth: 'auth' });
    getConversationMessagesApiV1ConversationsConversationIdMessagesGet.mockResolvedValue({ data: null });

    const result = await getConversationMessagesPage('conv-1');

    expect(result).toEqual({ items: [], next_cursor: null, prev_cursor: null });
  });
});

