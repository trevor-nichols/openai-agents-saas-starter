import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  changeCurrentUserEmailRequest,
  disableCurrentUserAccountRequest,
  fetchCurrentUserProfile,
  updateCurrentUserProfileRequest,
} from '@/lib/api/users';
import type {
  CurrentUserProfileResponseData,
  UserAccountDisableRequest,
  UserEmailChangeRequest,
  UserProfileUpdateRequest,
} from '@/lib/api/client/types.gen';
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

export function useUpdateCurrentUserProfileMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserProfileUpdateRequest) => updateCurrentUserProfileRequest(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.users.profile(), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.account.profile() });
    },
  });
}

export function useChangeCurrentUserEmailMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserEmailChangeRequest) => changeCurrentUserEmailRequest(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(
        queryKeys.users.profile(),
        (prev) =>
          prev
            ? ({
                ...(prev as CurrentUserProfileResponseData),
                email: data.email,
                email_verified: data.email_verified,
              } satisfies CurrentUserProfileResponseData)
            : prev,
      );
      queryClient.invalidateQueries({ queryKey: queryKeys.account.profile() });
    },
  });
}

export function useDisableCurrentUserAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserAccountDisableRequest) => disableCurrentUserAccountRequest(payload),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: queryKeys.users.profile() });
      queryClient.removeQueries({ queryKey: queryKeys.account.profile() });
    },
  });
}
