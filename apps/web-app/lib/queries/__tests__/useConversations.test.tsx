import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useConversations } from '../conversations';
import { createQueryWrapper } from '@/lib/chat/__tests__/testUtils';
import type { ConversationListPage } from '@/types/conversations';

vi.mock('@/lib/api/conversations', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api/conversations')>();
  return {
    ...actual,
    fetchConversationsPage: vi.fn(),
  };
});

const { fetchConversationsPage } = vi.mocked(await import('@/lib/api/conversations'));

afterEach(() => {
  vi.clearAllMocks();
});

describe('useConversations pagination state', () => {
  it('drops stale cursors after local removal and refetches from the start', async () => {
    const firstPage: ConversationListPage = {
      items: [
        { id: 'conv-3', updated_at: '2025-02-03T00:00:00.000Z' },
        { id: 'conv-2', updated_at: '2025-02-02T00:00:00.000Z' },
      ],
      next_cursor: 'cursor-2',
    };
    const secondPage: ConversationListPage = {
      items: [{ id: 'conv-1', updated_at: '2025-02-01T00:00:00.000Z' }],
      next_cursor: null,
    };
    const refetchedFirstPage: ConversationListPage = {
      items: [
        { id: 'conv-3', updated_at: '2025-02-03T00:00:00.000Z' },
        { id: 'conv-1', updated_at: '2025-02-01T00:00:00.000Z' },
      ],
      next_cursor: 'cursor-1-new',
    };
    const refetchedSecondPage: ConversationListPage = {
      items: [{ id: 'conv-0', updated_at: '2025-01-31T00:00:00.000Z' }],
      next_cursor: null,
    };

    fetchConversationsPage.mockResolvedValueOnce(firstPage);
    fetchConversationsPage.mockResolvedValueOnce(secondPage);
    fetchConversationsPage.mockResolvedValueOnce(refetchedFirstPage);
    fetchConversationsPage.mockResolvedValueOnce(refetchedSecondPage);

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useConversations(), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.isLoadingConversations).toBe(false));
    expect(result.current.conversationList.map((c) => c.id)).toEqual(['conv-3', 'conv-2']);

    await act(async () => {
      result.current.loadMore();
    });
    await waitFor(() =>
      expect(result.current.conversationList.map((c) => c.id)).toEqual(['conv-3', 'conv-2', 'conv-1']),
    );
    expect(fetchConversationsPage).toHaveBeenNthCalledWith(2, { limit: 50, cursor: 'cursor-2' });

    act(() => result.current.removeConversationFromList('conv-2'));
    await waitFor(() => expect(result.current.conversationList.map((c) => c.id)).toEqual(['conv-3', 'conv-1']));

    await waitFor(() => expect(fetchConversationsPage).toHaveBeenCalledTimes(3));
    expect(fetchConversationsPage).toHaveBeenNthCalledWith(3, { limit: 50, cursor: null });

    await waitFor(() => expect(result.current.hasNextPage).toBe(true));

    await act(async () => {
      result.current.loadMore();
    });
    await waitFor(() =>
      expect(result.current.conversationList.map((c) => c.id)).toEqual(['conv-3', 'conv-1', 'conv-0']),
    );
    expect(fetchConversationsPage).toHaveBeenNthCalledWith(4, { limit: 50, cursor: 'cursor-1-new' });
  });
});
