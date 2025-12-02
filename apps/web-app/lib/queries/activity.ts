/**
 * Activity log queries (tenant-scoped audit events)
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { fetchActivityPage } from '@/lib/api/activity';
import { queryKeys } from './keys';
import type { ActivityEvent } from '@/types/activity';

interface UseActivityFeedReturn {
  activity: ActivityEvent[];
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useActivityFeed(params?: { limit?: number }): UseActivityFeedReturn {
  const queryClient = useQueryClient();
  const limit = params?.limit ?? 20;

  const {
    data,
    isLoading,
    error,
  } = useQuery({
    queryKey: queryKeys.activity.list({ limit }),
    queryFn: () => fetchActivityPage({ limit }),
    staleTime: 15 * 1000,
  });

  const activity = useMemo(() => data?.items ?? [], [data?.items]);

  const refresh = useCallback(() => {
    void queryClient.invalidateQueries({ queryKey: queryKeys.activity.list({ limit }) });
  }, [limit, queryClient]);

  return {
    activity,
    isLoading,
    error: error?.message ?? null,
    refresh,
  };
}
