import { useCallback, useMemo, useState } from 'react';
import { useInfiniteQuery, useQuery } from '@tanstack/react-query';

import {
  fetchConversationLedgerEvents,
  fetchConversationMessages,
} from '@/lib/api/conversations';
import { queryKeys } from '@/lib/queries/keys';
import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import type { ConversationMessagesPage } from '@/types/conversations';

import type { ChatMessage } from '../types';
import { dedupeAndSortMessages, mapMessagesToChatMessages } from '../mappers/chatRequestMappers';
import { extractMemoryCheckpointMarkers } from '../mappers/ledgerReplayMappers';

export interface UseConversationHistoryResult {
  historyMessagesWithMarkers: ChatMessage[];
  ledgerEvents: PublicSseEvent[] | undefined;
  isLoadingHistory: boolean;
  historyError: string | null;
  hasOlderMessages: boolean;
  isFetchingOlderMessages: boolean;
  loadOlderMessages: () => Promise<void>;
  retryMessages: () => void;
  clearHistoryError: () => void;
}

export function useConversationHistory(conversationId: string | null): UseConversationHistoryResult {
  const [manualHistoryError, setManualHistoryError] = useState<string | null>(null);
  const [dismissedQueryErrorKey, setDismissedQueryErrorKey] = useState<string | null>(null);

  const messagesQueryKey = useMemo(
    () => queryKeys.conversations.messages(conversationId ?? 'preview'),
    [conversationId],
  );
  const ledgerQueryKey = useMemo(
    () => queryKeys.conversations.ledger(conversationId ?? 'preview'),
    [conversationId],
  );

  const {
    data: messagesPages,
    isLoading: isLoadingMessages,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    error: messagesError,
    refetch: refetchMessages,
  } = useInfiniteQuery<ConversationMessagesPage>({
    queryKey: messagesQueryKey,
    enabled: Boolean(conversationId),
    queryFn: ({ pageParam }) =>
      fetchConversationMessages({
        conversationId: conversationId as string,
        limit: 50,
        cursor: (pageParam as string | null) ?? null,
        direction: 'desc',
      }),
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: null as string | null,
    staleTime: 30 * 1000,
    retry: false,
  });

  const { data: ledgerEvents } = useQuery<PublicSseEvent[]>({
    queryKey: ledgerQueryKey,
    enabled: Boolean(conversationId),
    queryFn: () => fetchConversationLedgerEvents({ conversationId: conversationId as string }),
    staleTime: 30 * 1000,
    retry: false,
  });

  const historyMessages = useMemo(() => {
    if (!messagesPages?.pages) return [] as ChatMessage[];
    const flattened = messagesPages.pages.flatMap(
      (page: ConversationMessagesPage) => page.items ?? [],
    );
    return dedupeAndSortMessages(mapMessagesToChatMessages(flattened, conversationId ?? undefined));
  }, [conversationId, messagesPages]);

  const checkpointMarkers = useMemo(
    () => (ledgerEvents?.length ? extractMemoryCheckpointMarkers(ledgerEvents) : []),
    [ledgerEvents],
  );

  const historyMessagesWithMarkers = useMemo(
    () => dedupeAndSortMessages([...historyMessages, ...checkpointMarkers]),
    [historyMessages, checkpointMarkers],
  );

  const isLoadingHistory = Boolean(conversationId) && isLoadingMessages && !messagesPages;

  const queryHistoryErrorMessage = useMemo(() => {
    if (!messagesError) return null;
    return messagesError instanceof Error ? messagesError.message : 'Failed to load conversation messages.';
  }, [messagesError]);

  const queryHistoryErrorKey = useMemo(() => {
    if (!queryHistoryErrorMessage) return null;
    return `${conversationId ?? 'preview'}:${queryHistoryErrorMessage}`;
  }, [conversationId, queryHistoryErrorMessage]);

  const historyError = useMemo(() => {
    if (manualHistoryError) return manualHistoryError;
    if (!queryHistoryErrorKey || queryHistoryErrorKey === dismissedQueryErrorKey) return null;
    return queryHistoryErrorMessage;
  }, [
    dismissedQueryErrorKey,
    manualHistoryError,
    queryHistoryErrorKey,
    queryHistoryErrorMessage,
  ]);

  const loadOlderMessages = useCallback(async () => {
    if (!hasNextPage) return;
    try {
      await fetchNextPage();
    } catch (error) {
      console.error('[useConversationHistory] Failed to load older messages:', error);
      setManualHistoryError(
        error instanceof Error ? error.message : 'Failed to load older messages.',
      );
    }
  }, [fetchNextPage, hasNextPage]);

  const retryMessages = useCallback(() => {
    setManualHistoryError(null);
    setDismissedQueryErrorKey(null);
    void refetchMessages();
  }, [refetchMessages]);

  const clearHistoryError = useCallback(() => {
    setManualHistoryError(null);
    setDismissedQueryErrorKey(queryHistoryErrorKey ?? null);
  }, [queryHistoryErrorKey]);

  return {
    historyMessagesWithMarkers,
    ledgerEvents,
    isLoadingHistory,
    historyError,
    hasOlderMessages: Boolean(hasNextPage),
    isFetchingOlderMessages: isFetchingNextPage,
    loadOlderMessages,
    retryMessages,
    clearHistoryError,
  };
}
