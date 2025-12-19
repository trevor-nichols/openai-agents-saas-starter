import { useQuery } from '@tanstack/react-query';

import { fetchCurrentUserProfile } from '@/lib/api/users';
import { queryKeys } from './keys';

export function useCurrentUserProfileQuery(options?: { enabled?: boolean }) {
  const query = useQuery({
    queryKey: queryKeys.users.profile(),
    queryFn: fetchCurrentUserProfile,
    enabled: options?.enabled ?? true,
    staleTime: 30 * 1000,
  });

  return {
    profile: query.data ?? null,
    isLoadingProfile: query.isLoading,
    profileError: query.error instanceof Error ? query.error : null,
    refetchProfile: query.refetch,
  };
}
