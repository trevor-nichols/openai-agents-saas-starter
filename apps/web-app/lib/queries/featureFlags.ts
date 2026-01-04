import { useQuery } from '@tanstack/react-query';

import { fetchFeatureFlags } from '@/lib/api/featureFlags';
import type { FeatureFlags } from '@/types/features';
import { queryKeys } from './keys';

interface UseFeatureFlagsResult {
  flags: FeatureFlags | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => void;
}

export function useFeatureFlags(): UseFeatureFlagsResult {
  const query = useQuery({
    queryKey: queryKeys.features.flags(),
    queryFn: fetchFeatureFlags,
    staleTime: 30 * 1000,
    refetchOnWindowFocus: false,
  });

  return {
    flags: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refetch: () => {
      void query.refetch();
    },
  };
}
