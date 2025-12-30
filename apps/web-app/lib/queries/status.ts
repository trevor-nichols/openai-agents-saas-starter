import { useQuery } from '@tanstack/react-query';

import { fetchPlatformStatusSnapshot } from '@/lib/api/status';
import type { PlatformStatusSnapshot } from '@/types/status';
import { queryKeys } from './keys';

interface UsePlatformStatusResult {
  status: PlatformStatusSnapshot | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

interface UsePlatformStatusQueryOptions {
  enabled?: boolean;
}

export function usePlatformStatusQuery(options: UsePlatformStatusQueryOptions = {}): UsePlatformStatusResult {
  const enabled = options.enabled ?? typeof window !== 'undefined';
  const query = useQuery({
    queryKey: queryKeys.status.snapshot(),
    queryFn: fetchPlatformStatusSnapshot,
    staleTime: 60 * 1000,
    refetchOnWindowFocus: false,
    enabled,
  });

  return {
    status: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refetch: () => {
      void query.refetch();
    },
  };
}
