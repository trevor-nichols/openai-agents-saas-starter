import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  acceptTeamInviteExisting,
  addTeamMember,
  fetchTeamInvites,
  fetchTeamMembers,
  issueTeamInvite,
  removeTeamMember,
  revokeTeamInvite,
  updateTeamMemberRole,
} from '@/lib/api/team';
import type {
  AddTeamMemberInput,
  IssueTeamInviteInput,
  TeamInviteIssueResult,
  TeamInviteListFilters,
  TeamInviteListResult,
  TeamInviteSummary,
  TeamMemberListFilters,
  TeamMemberListResult,
  TeamMemberSummary,
  UpdateTeamMemberRoleInput,
} from '@/types/team';

import { queryKeys } from './keys';

const DEFAULT_LIMIT = 50;

export function useTeamMembersQuery(filters: TeamMemberListFilters = {}) {
  const normalized: TeamMemberListFilters = {
    limit: filters.limit ?? DEFAULT_LIMIT,
    offset: filters.offset ?? 0,
  };

  const queryKeyFilters = {
    limit: normalized.limit,
    offset: normalized.offset,
  };

  return useQuery<TeamMemberListResult>({
    queryKey: queryKeys.team.members.list(queryKeyFilters),
    queryFn: () => fetchTeamMembers(normalized),
    staleTime: 30 * 1000,
    placeholderData: (previous) => previous,
  });
}

export function useAddTeamMemberMutation() {
  const queryClient = useQueryClient();
  return useMutation<TeamMemberSummary, Error, AddTeamMemberInput>({
    mutationFn: (payload) => addTeamMember(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team.members.all() });
    },
  });
}

export function useUpdateTeamMemberRoleMutation() {
  const queryClient = useQueryClient();
  return useMutation<TeamMemberSummary, Error, { userId: string; payload: UpdateTeamMemberRoleInput }>(
    {
      mutationFn: ({ userId, payload }) => updateTeamMemberRole(userId, payload),
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: queryKeys.team.members.all() });
      },
    },
  );
}

export function useRemoveTeamMemberMutation() {
  const queryClient = useQueryClient();
  return useMutation<string, Error, { userId: string }>({
    mutationFn: ({ userId }) => removeTeamMember(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team.members.all() });
    },
  });
}

export function useTeamInvitesQuery(filters: TeamInviteListFilters = {}) {
  const normalized: TeamInviteListFilters = {
    status: filters.status ?? undefined,
    email: filters.email ?? undefined,
    limit: filters.limit ?? DEFAULT_LIMIT,
    offset: filters.offset ?? 0,
  };

  const queryKeyFilters = {
    status: normalized.status ?? null,
    email: normalized.email ?? null,
    limit: normalized.limit,
    offset: normalized.offset,
  };

  return useQuery<TeamInviteListResult>({
    queryKey: queryKeys.team.invites.list(queryKeyFilters),
    queryFn: () => fetchTeamInvites(normalized),
    staleTime: 30 * 1000,
    placeholderData: (previous) => previous,
  });
}

export function useIssueTeamInviteMutation() {
  const queryClient = useQueryClient();
  return useMutation<TeamInviteIssueResult, Error, IssueTeamInviteInput>({
    mutationFn: (payload) => issueTeamInvite(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team.invites.all() });
    },
  });
}

export function useRevokeTeamInviteMutation() {
  const queryClient = useQueryClient();
  return useMutation<TeamInviteSummary, Error, { inviteId: string }>({
    mutationFn: ({ inviteId }) => revokeTeamInvite(inviteId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team.invites.all() });
    },
  });
}

export function useAcceptTeamInviteExistingMutation() {
  const queryClient = useQueryClient();
  return useMutation<TeamInviteSummary, Error, { token: string }>({
    mutationFn: ({ token }) => acceptTeamInviteExisting(token),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.team.invites.all() });
      queryClient.invalidateQueries({ queryKey: queryKeys.team.members.all() });
    },
  });
}
