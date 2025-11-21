import { useQuery } from '@tanstack/react-query';

import { fetchTools } from '@/lib/api/tools';
import { queryKeys } from './keys';
import type { ToolRegistry } from '@/types/tools';

interface UseToolsResult {
  tools: ToolRegistry;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function useTools(): UseToolsResult {
  const {
    data = {},
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.tools.list(),
    queryFn: fetchTools,
    staleTime: 10 * 60 * 1000,
  });

  return {
    tools: data,
    isLoading,
    error: error?.message ?? null,
    refetch: () => refetch().then(() => undefined),
  };
}
