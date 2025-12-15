/**
 * TanStack Query hooks for conversations
 *
 * Professional structure:
 * - Uses centralized query keys
 * - Leverages API layer functions
 * - Provides optimistic updates
 * - Type-safe mutations
 */

import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import type {
  ConversationHistory,
  ConversationListItem,
  ConversationListPage,
  ConversationSearchResultItem,
  ConversationEvents,
  ConversationMemoryConfig,
  ConversationMemoryConfigInput,
} from '@/types/conversations';
import {
  fetchConversationsPage,
  fetchConversationHistory,
  fetchConversationEvents,
  sortConversationsByDate,
  searchConversations,
  updateConversationMemory as updateConversationMemoryApi,
} from '@/lib/api/conversations';
import { queryKeys } from './keys';
import type { InfiniteData } from '@tanstack/react-query';

interface UseConversationsReturn {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  isFetchingMoreConversations: boolean;
  loadMore: () => void;
  hasNextPage: boolean;
  loadConversations: () => void;
  error: string | null;
  addConversationToList: (newConversation: ConversationListItem) => void;
  updateConversationInList: (updatedConversation: ConversationListItem) => void;
  removeConversationFromList: (conversationId: string) => void;
}

interface UseConversationSearchReturn {
  results: ConversationSearchResultItem[];
  isLoading: boolean;
  isFetchingMore: boolean;
  loadMore: () => void;
  hasNextPage: boolean;
  error: string | null;
}

interface UseConversationDetailReturn {
  conversationHistory: ConversationHistory | null;
  isLoadingDetail: boolean;
  isFetchingDetail: boolean;
  detailError: string | null;
  refetchDetail: () => Promise<void>;
}

interface UseConversationEventsReturn {
  events: ConversationEvents | null;
  isLoadingEvents: boolean;
  isFetchingEvents: boolean;
  eventsError: string | null;
  refetchEvents: () => Promise<void>;
}

interface UseUpdateConversationMemoryReturn {
  updateMemory: (config: ConversationMemoryConfigInput) => Promise<ConversationMemoryConfig>;
  isUpdating: boolean;
  error: string | null;
}

/**
 * Hook to manage conversations list with TanStack Query
 *
 * Features:
 * - Automatic caching
 * - Background refetching
 * - Optimistic updates
 * - Error handling
 */
export function useConversations(): UseConversationsReturn {
  const queryClient = useQueryClient();

  const {
    data,
    isLoading: isLoadingConversations,
    isFetchingNextPage: isFetchingMoreConversations,
    error,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: queryKeys.conversations.lists(),
    queryFn: ({ pageParam }) =>
      fetchConversationsPage({ limit: 50, cursor: (pageParam as string | null) ?? null }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as string | null,
    staleTime: 30 * 1000,
  });

  const conversationList = useMemo(
    () => sortConversationsByDate((data?.pages ?? []).flatMap((page) => page.items)),
    [data?.pages],
  );

  const loadMore = useCallback(() => {
    if (hasNextPage && !isFetchingMoreConversations) {
      void fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isFetchingMoreConversations]);

  const loadConversations = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });
  }, [queryClient]);

  const applyLocalMutation = useCallback(
    (
      mutate: (items: ConversationListItem[]) => ConversationListItem[],
    ): InfiniteData<ConversationListPage> | undefined => {
      return queryClient.setQueryData<InfiniteData<ConversationListPage>>(
        queryKeys.conversations.lists(),
        (oldData) => {
          const flattened = (oldData?.pages ?? []).flatMap((p) => p.items);
          const nextItems = sortConversationsByDate(mutate(flattened));
          // Reset pagination metadata so the next fetch uses a fresh cursor from the server.
          return {
            pages: [
              {
                items: nextItems,
                next_cursor: null,
              },
            ],
            pageParams: [null],
          };
        },
      );
    },
    [queryClient],
  );

  // Optimistically add a conversation to the list
  const addConversationToList = useCallback(
    (newConversation: ConversationListItem) => {
      applyLocalMutation((items) => {
        const existingIndex = items.findIndex((c) => c.id === newConversation.id);
        if (existingIndex >= 0) {
          const next = [...items];
          next[existingIndex] = newConversation;
          return next;
        }
        return [newConversation, ...items];
      });
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });
    },
    [applyLocalMutation, queryClient],
  );

  // Optimistically update a conversation in the list
  const updateConversationInList = useCallback(
    (updatedConversation: ConversationListItem) => {
      applyLocalMutation((items) =>
        items.map((c) => (c.id === updatedConversation.id ? updatedConversation : c)),
      );
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });
    },
    [applyLocalMutation, queryClient],
  );

  const removeConversationFromList = useCallback(
    (conversationId: string) => {
      applyLocalMutation((items) => items.filter((conversation) => conversation.id !== conversationId));
      queryClient.removeQueries({ queryKey: queryKeys.conversations.detail(conversationId) });
      void queryClient.invalidateQueries({ queryKey: queryKeys.conversations.lists() });
    },
    [applyLocalMutation, queryClient],
  );

  return {
    conversationList,
    isLoadingConversations,
    isFetchingMoreConversations,
    loadMore,
    hasNextPage: Boolean(hasNextPage),
    loadConversations,
    error: error?.message ?? null,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
  };
}

export function useConversationSearch(query: string): UseConversationSearchReturn {
  const trimmedQuery = query?.trim() ?? '';
  const isActive = Boolean(trimmedQuery);

  const {
    data,
    isLoading,
    isFetchingNextPage: isFetchingMore,
    error,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: [...queryKeys.conversations.all, 'search', trimmedQuery],
    queryFn: ({ pageParam }) =>
      searchConversations({ query: trimmedQuery, limit: 20, cursor: (pageParam as string | null) ?? null }),
    enabled: isActive,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as string | null,
    staleTime: 10 * 1000,
  });

  const results = useMemo(
    () => (isActive ? (data?.pages ?? []).flatMap((page) => page.items) : []),
    [data?.pages, isActive],
  );

  const loadMore = useCallback(() => {
    if (isActive && hasNextPage && !isFetchingMore) {
      void fetchNextPage();
    }
  }, [fetchNextPage, hasNextPage, isActive, isFetchingMore]);

  return {
    results,
    isLoading: isActive ? isLoading : false,
    isFetchingMore: isActive ? isFetchingMore : false,
    loadMore,
    hasNextPage: isActive ? Boolean(hasNextPage) : false,
    error: isActive ? error?.message ?? null : null,
  };
}

export function useConversationDetail(conversationId: string | null): UseConversationDetailReturn {
  const isEnabled = Boolean(conversationId);
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.conversations.detail(conversationId ?? 'preview'),
    queryFn: () => fetchConversationHistory(conversationId as string),
    enabled: isEnabled,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return {
    conversationHistory: data ?? null,
    isLoadingDetail: isLoading && isEnabled,
    isFetchingDetail: isFetching && isEnabled,
    detailError: error?.message ?? null,
    refetchDetail: () => refetch().then(() => undefined),
  };
}

export function useConversationEvents(
  conversationId: string | null,
  options?: { workflowRunId?: string | null },
): UseConversationEventsReturn {
  const isEnabled = Boolean(conversationId);
  const {
    data,
    isLoading,
    isFetching,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.conversations.events(conversationId ?? 'preview', {
      workflowRunId: options?.workflowRunId ?? null,
    }),
    queryFn: () =>
      fetchConversationEvents({
        conversationId: conversationId as string,
        workflowRunId: options?.workflowRunId ?? null,
      }),
    enabled: isEnabled,
    staleTime: 5 * 60 * 1000,
    retry: 1,
  });

  return {
    events: data ?? null,
    isLoadingEvents: isLoading && isEnabled,
    isFetchingEvents: isFetching && isEnabled,
    eventsError: error?.message ?? null,
    refetchEvents: () => refetch().then(() => undefined),
  };
}

/**
 * Mutation hook to update conversation memory configuration.
 */
export function useUpdateConversationMemory(
  conversationId: string | null,
): UseUpdateConversationMemoryReturn {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationKey: [...queryKeys.conversations.all, 'memory', conversationId ?? 'none'],
    mutationFn: async (config: ConversationMemoryConfigInput) => {
      if (!conversationId) {
        throw new Error('Conversation id is required.');
      }
      return updateConversationMemoryApi({ conversationId, config });
    },
    onSuccess: () => {
      if (!conversationId) return;
      // Refresh conversation detail to reflect new memory defaults.
      void queryClient.invalidateQueries({
        queryKey: queryKeys.conversations.detail(conversationId),
      });
      // No list-level invalidation needed unless UI surfaces memory in list.
      // If future UI includes memory badges, we can invalidate lists here.
    },
  });

  return {
    updateMemory: mutation.mutateAsync,
    isUpdating: mutation.isPending,
    error: mutation.error instanceof Error ? mutation.error.message : null,
  };
}
