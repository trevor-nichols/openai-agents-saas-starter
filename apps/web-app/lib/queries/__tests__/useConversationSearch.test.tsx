import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useConversationSearch } from '../conversations';
import { createQueryWrapper } from '@/lib/chat/__tests__/testUtils';
import type { ConversationSearchPage } from '@/types/conversations';

vi.mock('@/lib/api/conversations', () => ({
  searchConversations: vi.fn(),
}));

const { searchConversations } = vi.mocked(await import('@/lib/api/conversations'));

afterEach(() => {
  vi.clearAllMocks();
  vi.restoreAllMocks();
});

describe('useConversationSearch', () => {
  it('returns search results and exposes pagination flag', async () => {
    const firstPage: ConversationSearchPage = {
      items: [
        {
          conversation_id: 'conv-1',
          preview: 'matched snippet',
          updated_at: '2025-01-01T00:00:00.000Z',
          score: 0.9,
        },
      ],
      next_cursor: 'cursor-1',
    };
    searchConversations.mockResolvedValueOnce(firstPage);

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useConversationSearch('alpha'), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.results).toEqual(firstPage.items);
    expect(result.current.hasNextPage).toBe(true);
    expect(searchConversations).toHaveBeenCalledWith({
      query: 'alpha',
      limit: 20,
      cursor: null,
    });
  });

  it('loads the next page when loadMore is called', async () => {
    const firstPage: ConversationSearchPage = {
      items: [{ conversation_id: 'conv-1', preview: 'first', updated_at: '2025-01-01T00:00:00.000Z' }],
      next_cursor: 'cursor-1',
    };
    const secondPage: ConversationSearchPage = {
      items: [{ conversation_id: 'conv-2', preview: 'second', updated_at: '2025-01-01T00:01:00.000Z' }],
      next_cursor: null,
    };

    searchConversations.mockResolvedValueOnce(firstPage);
    searchConversations.mockResolvedValueOnce(secondPage);

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useConversationSearch('alpha'), { wrapper: Wrapper });

    await waitFor(() => expect(result.current.results).toHaveLength(1));
    expect(result.current.hasNextPage).toBe(true);

    await act(async () => {
      result.current.loadMore();
    });

    await waitFor(() => expect(result.current.results).toHaveLength(2));
    expect(result.current.results.map((hit) => hit.conversation_id)).toEqual(['conv-1', 'conv-2']);
    expect(searchConversations).toHaveBeenNthCalledWith(2, {
      query: 'alpha',
      limit: 20,
      cursor: 'cursor-1',
    });
  });

  it('clears results when the query becomes empty', async () => {
    const firstPage: ConversationSearchPage = {
      items: [
        {
          conversation_id: 'conv-1',
          preview: 'matched snippet',
          updated_at: '2025-01-01T00:00:00.000Z',
          score: 0.9,
        },
      ],
      next_cursor: null,
    };
    searchConversations.mockResolvedValueOnce(firstPage);

    const { Wrapper } = createQueryWrapper();
    const { result, rerender } = renderHook(
      ({ q }) => useConversationSearch(q),
      { wrapper: Wrapper, initialProps: { q: 'alpha' } },
    );

    await waitFor(() => expect(result.current.results).toHaveLength(1));

    rerender({ q: '' });

    await waitFor(() => expect(result.current.results).toHaveLength(0));
    expect(result.current.hasNextPage).toBe(false);
    expect(searchConversations).toHaveBeenCalledTimes(1);
  });
});
