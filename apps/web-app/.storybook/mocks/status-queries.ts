import { mockStatus } from '@/features/marketing/status/__stories__/fixtures';

export function usePlatformStatusQuery() {
  return {
    status: mockStatus,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}
