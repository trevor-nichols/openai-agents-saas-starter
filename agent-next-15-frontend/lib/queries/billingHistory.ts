import { useInfiniteQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import { fetchBillingHistory } from '@/lib/api/billingHistory';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import type { BillingEvent } from '@/types/billing';
import { queryKeys } from './keys';

interface UseBillingHistoryOptions {
  pageSize?: number;
}

interface UseBillingHistoryResult {
  events: BillingEvent[];
  isLoading: boolean;
  isFetchingMore: boolean;
  hasNextPage: boolean;
  loadMore: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function useBillingHistory(options?: UseBillingHistoryOptions): UseBillingHistoryResult {
  const meta = readClientSessionMeta();
  const tenantId = meta?.tenantId ?? null;
  const pageSize = options?.pageSize ?? 25;

  const queryResult = useInfiniteQuery({
    queryKey: queryKeys.billing.history(tenantId, { pageSize }),
    queryFn: ({ pageParam }) => {
      if (!tenantId) {
        return Promise.resolve({ items: [], next_cursor: null });
      }
      return fetchBillingHistory({
        tenantId,
        limit: pageSize,
        cursor: typeof pageParam === 'string' ? pageParam : null,
      });
    },
    enabled: Boolean(tenantId),
    initialPageParam: null as string | null,
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    staleTime: 30 * 1000,
  });

  const events = useMemo(() => {
    if (!queryResult.data) {
      return [];
    }
    return queryResult.data.pages.flatMap((page) => page.items);
  }, [queryResult.data]);

  return {
    events,
    isLoading: queryResult.isLoading,
    isFetchingMore: queryResult.isFetchingNextPage,
    hasNextPage: Boolean(queryResult.hasNextPage),
    loadMore: () => queryResult.fetchNextPage().then(() => undefined),
    refetch: () => queryResult.refetch().then(() => undefined),
  };
}
