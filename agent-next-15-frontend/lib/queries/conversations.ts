/**
 * TanStack Query hooks for conversations
 *
 * Professional structure:
 * - Uses centralized query keys
 * - Leverages API layer functions
 * - Provides optimistic updates
 * - Type-safe mutations
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';

import type { ConversationHistory, ConversationListItem } from '@/types/conversations';
import {
  fetchConversations,
  fetchConversationHistory,
  sortConversationsByDate,
} from '@/lib/api/conversations';
import { queryKeys } from './keys';

interface UseConversationsReturn {
  conversationList: ConversationListItem[];
  isLoadingConversations: boolean;
  loadConversations: () => void;
  error: string | null;
  addConversationToList: (newConversation: ConversationListItem) => void;
  updateConversationInList: (updatedConversation: ConversationListItem) => void;
  removeConversationFromList: (conversationId: string) => void;
}

interface UseConversationDetailReturn {
  conversationHistory: ConversationHistory | null;
  isLoadingDetail: boolean;
  isFetchingDetail: boolean;
  detailError: string | null;
  refetchDetail: () => Promise<void>;
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
    data: conversationList = [],
    isLoading: isLoadingConversations,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.conversations.lists(),
    queryFn: fetchConversations,
    staleTime: 30 * 1000, // Consider data fresh for 30 seconds
  });

  // Manual refetch function (maintains same API as before)
  const loadConversations = useCallback(() => {
    console.log('[useConversations] Manually refetching conversation list...');
    refetch();
  }, [refetch]);

  // Optimistically add a conversation to the list
  const addConversationToList = useCallback(
    (newConversation: ConversationListItem) => {
      queryClient.setQueryData<ConversationListItem[]>(
        queryKeys.conversations.lists(),
        (oldData = []) => {
          // If conversation already exists, update it; otherwise prepend
          const exists = oldData.find((c) => c.id === newConversation.id);

          if (exists) {
            return sortConversationsByDate(
              oldData.map((c) => (c.id === newConversation.id ? newConversation : c))
            );
          }

          return sortConversationsByDate([newConversation, ...oldData]);
        }
      );
    },
    [queryClient]
  );

  // Optimistically update a conversation in the list
  const updateConversationInList = useCallback(
    (updatedConversation: ConversationListItem) => {
      queryClient.setQueryData<ConversationListItem[]>(
        queryKeys.conversations.lists(),
        (oldData = []) => {
          return sortConversationsByDate(
            oldData.map((c) =>
              c.id === updatedConversation.id ? updatedConversation : c
            )
          );
        }
      );
    },
    [queryClient]
  );

  const removeConversationFromList = useCallback(
    (conversationId: string) => {
      queryClient.setQueryData<ConversationListItem[]>(
        queryKeys.conversations.lists(),
        (oldData = []) => oldData.filter((conversation) => conversation.id !== conversationId),
      );
      queryClient.removeQueries({ queryKey: queryKeys.conversations.detail(conversationId) });
    },
    [queryClient],
  );

  return {
    conversationList,
    isLoadingConversations,
    loadConversations,
    error: error?.message ?? null,
    addConversationToList,
    updateConversationInList,
    removeConversationFromList,
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
