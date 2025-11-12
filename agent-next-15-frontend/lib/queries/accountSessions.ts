import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  fetchUserSessions,
  logoutAllSessionsRequest,
  revokeSessionRequest,
  type SessionListParams,
  type SessionListPayload,
} from '@/lib/api/accountSessions';
import type { UserSessionItem } from '@/lib/api/client/types.gen';
import { queryKeys } from '@/lib/queries/keys';

export type UseUserSessionsOptions = SessionListParams;

export function useUserSessionsQuery(options: UseUserSessionsOptions = {}) {
  const limit = options.limit ?? 20;
  const offset = options.offset ?? 0;
  const tenantId = options.tenantId ?? null;
  const includeRevoked = options.includeRevoked ?? false;
  return useQuery<SessionListPayload>({
    queryKey: queryKeys.account.sessions.list({ limit, offset, tenantId, includeRevoked }),
    queryFn: () => fetchUserSessions({ ...options, limit, offset, tenantId, includeRevoked }),
    staleTime: 15 * 1000,
  });
}

export function useRevokeSessionMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: string) => revokeSessionRequest(sessionId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.account.sessions.all() });
    },
  });
}

export function useLogoutAllSessionsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => logoutAllSessionsRequest(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.account.sessions.all() });
    },
  });
}

export type SessionRow = UserSessionItem;
