'use client';

import { useMemo } from 'react';
import { useWorkflowRunsInfiniteQuery } from '@/lib/queries/workflows';
import type { WorkflowRunListFilters, WorkflowRunListItemView } from '@/lib/workflows/types';

export function useWorkflowRunsInfinite(filters: WorkflowRunListFilters) {
  const query = useWorkflowRunsInfiniteQuery(filters);

  const runs = useMemo<WorkflowRunListItemView[]>(
    () => query.data?.pages.flatMap((page) => page.items) ?? [],
    [query.data],
  );

  const hasMore = Boolean(query.data?.pages[query.data.pages.length - 1]?.next_cursor);

  return {
    runs,
    hasMore,
    isInitialLoading: query.isLoading && runs.length === 0,
    isLoadingMore: query.isFetchingNextPage,
    loadMore: query.hasNextPage ? query.fetchNextPage : undefined,
    refetch: query.refetch,
  };
}
