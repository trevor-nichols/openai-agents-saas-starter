/**
 * Activity log queries (tenant-scoped audit events)
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';

import { fetchActivityPage } from '@/lib/api/activity';
import { queryKeys } from './keys';
import type { ActivityEvent } from '@/types/activity';
import { mergeActivityEvents, toActivityDisplayItem } from '@/lib/utils/activity';
import { useActivityStream } from './useActivityStream';

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

export interface RecentActivityItem extends ReturnType<typeof toActivityDisplayItem> {}

interface UseRecentActivityReturn {
  items: RecentActivityItem[];
  badgeCount: number;
  streamStatus: 'idle' | 'connecting' | 'open' | 'closed' | 'error';
  isLoading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useRecentActivity(options?: { limit?: number; live?: boolean }): UseRecentActivityReturn {
  const limit = options?.limit ?? 8;
  const liveEnabled = options?.live ?? true;

  const {
    activity,
    isLoading,
    error,
    refresh,
  } = useActivityFeed({ limit: limit * 2 });

  const { events: liveEvents, status: streamStatus } = useActivityStream({ enabled: liveEnabled });

  const merged = useMemo(
    () => mergeActivityEvents(liveEvents, activity, limit),
    [activity, liveEvents, limit],
  );

  const items = useMemo(() => merged.map(toActivityDisplayItem), [merged]);

  return {
    items,
    badgeCount: merged.length,
    streamStatus,
    isLoading,
    error,
    refresh,
  } satisfies UseRecentActivityReturn;
}
