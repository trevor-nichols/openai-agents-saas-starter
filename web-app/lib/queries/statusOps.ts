import { useInfiniteQuery, useMutation } from '@tanstack/react-query';

import {
  fetchStatusSubscriptions,
  resendIncident,
  type ResendIncidentInput,
  type StatusSubscriptionsFilters,
} from '@/lib/api/statusOps';
import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { queryKeys } from './keys';

const DEFAULT_PAGE_SIZE = 25;

export interface UseStatusSubscriptionsResult {
  subscriptions: StatusSubscriptionSummary[];
  nextCursor: string | null;
  isLoading: boolean;
  isError: boolean;
  error: Error | null;
  isFetchingNextPage: boolean;
  hasNextPage: boolean;
  fetchNextPage: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function useStatusSubscriptionsQuery(
  filters: StatusSubscriptionsFilters = {},
  pageSize: number = DEFAULT_PAGE_SIZE,
): UseStatusSubscriptionsResult {
  const normalizedFilters: StatusSubscriptionsFilters = {
    ...filters,
    limit: filters.limit ?? pageSize,
  };

  const query = useInfiniteQuery({
    queryKey: queryKeys.statusOps.subscriptions(normalizedFilters as Record<string, unknown>),
    initialPageParam: normalizedFilters.cursor ?? null,
    queryFn: ({ pageParam }) =>
      fetchStatusSubscriptions({
        ...normalizedFilters,
        cursor: pageParam ?? null,
      }),
    getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
    staleTime: 30_000,
    refetchOnWindowFocus: false,
  });

  const subscriptions = query.data?.pages.flatMap((page) => page.items) ?? [];
  const lastPage = query.data?.pages.at(-1);

  return {
    subscriptions,
    nextCursor: lastPage?.nextCursor ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: (query.error as Error) ?? null,
    isFetchingNextPage: query.isFetchingNextPage,
    hasNextPage: Boolean(query.hasNextPage),
    fetchNextPage: async () => {
      await query.fetchNextPage();
    },
    refetch: async () => {
      await query.refetch();
    },
  };
}

export function useResendIncidentMutation() {
  return useMutation({
    mutationFn: (input: ResendIncidentInput) => resendIncident(input),
  });
}
