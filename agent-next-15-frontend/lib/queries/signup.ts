import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  approveSignupRequestAction,
  fetchSignupInvites,
  fetchSignupPolicy,
  fetchSignupRequests,
  issueSignupInviteRequest,
  rejectSignupRequestAction,
  revokeSignupInviteRequest,
  submitSignupAccessRequest,
} from '@/lib/api/signup';
import { queryKeys } from '@/lib/queries/keys';
import type {
  ApproveSignupRequestInput,
  SignupAccessRequestInput,
  IssueSignupInviteInput,
  RejectSignupRequestInput,
  SignupAccessPolicy,
  SignupInviteIssueResult,
  SignupInviteListFilters,
  SignupInviteListResult,
  SignupInviteSummary,
  SignupRequestDecisionResult,
  SignupRequestListFilters,
  SignupRequestListResult,
} from '@/types/signup';

const DEFAULT_INVITE_LIMIT = 25;
const DEFAULT_REQUEST_LIMIT = 25;

export function useSignupPolicyQuery() {
  return useQuery<SignupAccessPolicy>({
    queryKey: queryKeys.signup.policy(),
    queryFn: fetchSignupPolicy,
    staleTime: 5 * 60 * 1000,
  });
}

export function useSignupInvitesQuery(filters: SignupInviteListFilters = {}) {
  const normalized: SignupInviteListFilters = {
    status: filters.status ?? undefined,
    email: filters.email ?? undefined,
    requestId: filters.requestId ?? undefined,
    limit: filters.limit ?? DEFAULT_INVITE_LIMIT,
    offset: filters.offset ?? 0,
  };

  const queryKeyFilters: Record<string, unknown> = {
    status: normalized.status ?? null,
    email: normalized.email ?? null,
    requestId: normalized.requestId ?? null,
    limit: normalized.limit,
    offset: normalized.offset,
  };

  return useQuery<SignupInviteListResult>({
    queryKey: queryKeys.signup.invites.list(queryKeyFilters),
    queryFn: () => fetchSignupInvites(normalized),
    staleTime: 30 * 1000,
    placeholderData: (previous) => previous,
  });
}

export function useSignupRequestsQuery(filters: SignupRequestListFilters = {}) {
  const normalized: SignupRequestListFilters = {
    status: filters.status ?? undefined,
    limit: filters.limit ?? DEFAULT_REQUEST_LIMIT,
    offset: filters.offset ?? 0,
  };

  const queryKeyFilters: Record<string, unknown> = {
    status: normalized.status ?? null,
    limit: normalized.limit,
    offset: normalized.offset,
  };

  return useQuery<SignupRequestListResult>({
    queryKey: queryKeys.signup.requests.list(queryKeyFilters),
    queryFn: () => fetchSignupRequests(normalized),
    staleTime: 30 * 1000,
    placeholderData: (previous) => previous,
  });
}

export function useIssueSignupInviteMutation() {
  const queryClient = useQueryClient();
  return useMutation<SignupInviteIssueResult, Error, IssueSignupInviteInput>({
    mutationFn: (payload) => issueSignupInviteRequest(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.invites.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.requests.all() });
    },
  });
}

export function useRevokeSignupInviteMutation() {
  const queryClient = useQueryClient();
  return useMutation<SignupInviteSummary, Error, { inviteId: string }>({
    mutationFn: ({ inviteId }) => revokeSignupInviteRequest(inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.invites.all() });
    },
  });
}

export function useApproveSignupRequestMutation() {
  const queryClient = useQueryClient();
  return useMutation<
    SignupRequestDecisionResult,
    Error,
    { requestId: string; payload: ApproveSignupRequestInput }
  >({
    mutationFn: ({ requestId, payload }) => approveSignupRequestAction(requestId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.requests.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.invites.all() });
    },
  });
}

export function useRejectSignupRequestMutation() {
  const queryClient = useQueryClient();
  return useMutation<
    SignupRequestDecisionResult,
    Error,
    { requestId: string; payload: RejectSignupRequestInput }
  >({
    mutationFn: ({ requestId, payload }) => rejectSignupRequestAction(requestId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.signup.requests.all() });
    },
  });
}

export function useSubmitSignupAccessRequestMutation() {
  return useMutation<SignupAccessPolicy, Error, SignupAccessRequestInput>({
    mutationFn: (payload) => submitSignupAccessRequest(payload),
  });
}
