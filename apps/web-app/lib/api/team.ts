import { apiV1Path } from '@/lib/apiPaths';
import type {
  AddTeamMemberInput,
  IssueTeamInviteInput,
  TeamInviteListFilters,
  TeamInviteListResult,
  TeamInviteIssueResult,
  TeamInviteSummary,
  TeamMemberListFilters,
  TeamMemberListResult,
  TeamMemberSummary,
  UpdateTeamMemberRoleInput,
} from '@/types/team';

interface ListMembersResponse {
  success: boolean;
  members?: TeamMemberSummary[];
  total?: number;
  limit?: number;
  offset?: number;
  error?: string;
}

interface ListInvitesResponse {
  success: boolean;
  invites?: TeamInviteSummary[];
  total?: number;
  limit?: number;
  offset?: number;
  error?: string;
}

interface ApiResponse<TData> {
  success: boolean;
  data?: TData;
  message?: string;
  error?: string;
}

function createError(response: Response, fallbackMessage: string, detail?: string): Error {
  const base =
    detail ||
    (response.status === 401
      ? 'You have been signed out. Please log back in.'
      : fallbackMessage);
  return new Error(base);
}

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse API response.');
  }
}

function extractErrorMessage(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined;
  }
  const record = payload as Record<string, unknown>;
  const detail = record.error ?? record.message ?? record.detail;
  return typeof detail === 'string' ? detail : undefined;
}

export async function fetchTeamMembers(
  filters: TeamMemberListFilters = {},
): Promise<TeamMemberListResult> {
  const search = new URLSearchParams();
  if (typeof filters.limit === 'number') {
    search.set('limit', String(filters.limit));
  }
  if (typeof filters.offset === 'number') {
    search.set('offset', String(filters.offset));
  }

  const response = await fetch(
    apiV1Path(`/tenants/members${search.size > 0 ? `?${search.toString()}` : ''}`),
    { cache: 'no-store' },
  );

  const payload = await parseJson<ListMembersResponse>(response);

  if (!response.ok || payload.success === false || !Array.isArray(payload.members)) {
    throw createError(response, 'Unable to load team members.', extractErrorMessage(payload));
  }

  return {
    members: payload.members,
    total: payload.total ?? payload.members.length,
    limit: payload.limit ?? filters.limit ?? payload.members.length,
    offset: payload.offset ?? filters.offset ?? 0,
  };
}

export async function addTeamMember(
  payload: AddTeamMemberInput,
): Promise<TeamMemberSummary> {
  const response = await fetch(apiV1Path('/tenants/members'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const result = await parseJson<ApiResponse<TeamMemberSummary>>(response);

  if (!response.ok || result.success === false || !result.data) {
    throw createError(response, 'Unable to add team member.', extractErrorMessage(result));
  }

  return result.data;
}

export async function updateTeamMemberRole(
  userId: string,
  payload: UpdateTeamMemberRoleInput,
): Promise<TeamMemberSummary> {
  if (!userId) {
    throw new Error('User id is required.');
  }

  const response = await fetch(
    apiV1Path(`/tenants/members/${encodeURIComponent(userId)}/role`),
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    },
  );

  const result = await parseJson<ApiResponse<TeamMemberSummary>>(response);

  if (!response.ok || result.success === false || !result.data) {
    throw createError(response, 'Unable to update member role.', extractErrorMessage(result));
  }

  return result.data;
}

export async function removeTeamMember(userId: string): Promise<string> {
  if (!userId) {
    throw new Error('User id is required.');
  }

  const response = await fetch(
    apiV1Path(`/tenants/members/${encodeURIComponent(userId)}`),
    {
      method: 'DELETE',
      cache: 'no-store',
    },
  );

  const result = await parseJson<ApiResponse<null>>(response);

  if (!response.ok || result.success === false) {
    throw createError(response, 'Unable to remove team member.', extractErrorMessage(result));
  }

  return result.message ?? 'Member removed successfully.';
}

export async function fetchTeamInvites(
  filters: TeamInviteListFilters = {},
): Promise<TeamInviteListResult> {
  const search = new URLSearchParams();
  if (filters.status) {
    search.set('status', filters.status);
  }
  if (filters.email) {
    search.set('email', filters.email);
  }
  if (typeof filters.limit === 'number') {
    search.set('limit', String(filters.limit));
  }
  if (typeof filters.offset === 'number') {
    search.set('offset', String(filters.offset));
  }

  const response = await fetch(
    apiV1Path(`/tenants/invites${search.size > 0 ? `?${search.toString()}` : ''}`),
    { cache: 'no-store' },
  );

  const payload = await parseJson<ListInvitesResponse>(response);

  if (!response.ok || payload.success === false || !Array.isArray(payload.invites)) {
    throw createError(response, 'Unable to load team invites.', extractErrorMessage(payload));
  }

  return {
    invites: payload.invites,
    total: payload.total ?? payload.invites.length,
    limit: payload.limit ?? filters.limit ?? payload.invites.length,
    offset: payload.offset ?? filters.offset ?? 0,
  };
}

export async function issueTeamInvite(
  payload: IssueTeamInviteInput,
): Promise<TeamInviteIssueResult> {
  const response = await fetch(apiV1Path('/tenants/invites'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const result = await parseJson<ApiResponse<TeamInviteIssueResult>>(response);

  if (!response.ok || result.success === false || !result.data) {
    throw createError(response, 'Unable to issue team invite.', extractErrorMessage(result));
  }

  return result.data;
}

export async function revokeTeamInvite(inviteId: string): Promise<TeamInviteSummary> {
  if (!inviteId) {
    throw new Error('Invite id is required.');
  }

  const response = await fetch(
    apiV1Path(`/tenants/invites/${encodeURIComponent(inviteId)}/revoke`),
    {
      method: 'POST',
      cache: 'no-store',
    },
  );

  const result = await parseJson<ApiResponse<TeamInviteSummary>>(response);

  if (!response.ok || result.success === false || !result.data) {
    throw createError(response, 'Unable to revoke team invite.', extractErrorMessage(result));
  }

  return result.data;
}

export async function acceptTeamInviteExisting(token: string): Promise<TeamInviteSummary> {
  if (!token) {
    throw new Error('Invite token is required.');
  }

  const response = await fetch(apiV1Path('/tenants/invites/accept/current'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ token }),
    cache: 'no-store',
  });

  const result = await parseJson<ApiResponse<TeamInviteSummary>>(response);

  if (!response.ok || result.success === false || !result.data) {
    throw createError(response, 'Unable to accept invite.', extractErrorMessage(result));
  }

  return result.data;
}
