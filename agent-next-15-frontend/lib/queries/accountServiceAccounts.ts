import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  fetchServiceAccountTokens,
  issueServiceAccountTokenRequest,
  revokeServiceAccountTokenRequest,
  type ServiceAccountTokenQueryParams,
} from '@/lib/api/accountServiceAccounts';
import { queryKeys } from '@/lib/queries/keys';
import type {
  ServiceAccountIssuePayload,
  ServiceAccountIssueResult,
  ServiceAccountTokenListResult,
} from '@/types/serviceAccounts';

const DEFAULT_LIMIT = 50;

export type UseServiceAccountTokensOptions = ServiceAccountTokenQueryParams;

export function useServiceAccountTokensQuery(options: UseServiceAccountTokensOptions = {}) {
  const normalized = {
    ...options,
    limit: options.limit ?? DEFAULT_LIMIT,
    offset: options.offset ?? 0,
  } satisfies ServiceAccountTokenQueryParams;

  return useQuery<ServiceAccountTokenListResult>({
    queryKey: queryKeys.account.serviceAccounts.list(normalized),
    queryFn: () => fetchServiceAccountTokens(normalized),
    staleTime: 30 * 1000,
    placeholderData: (previousData) => previousData,
  });
}

export function useRevokeServiceAccountTokenMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ tokenId, reason }: { tokenId: string; reason?: string }) =>
      revokeServiceAccountTokenRequest(tokenId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.account.serviceAccounts.all() });
    },
  });
}

export function useIssueServiceAccountTokenMutation() {
  const queryClient = useQueryClient();
  return useMutation<ServiceAccountIssueResult, Error, ServiceAccountIssuePayload>({
    mutationFn: (payload) => issueServiceAccountTokenRequest(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.account.serviceAccounts.all() });
    },
  });
}
