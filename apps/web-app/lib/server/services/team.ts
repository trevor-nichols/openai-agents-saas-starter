import 'server-only';

import {
  addMemberApiV1TenantsMembersPost,
  acceptInviteApiV1TenantsInvitesAcceptPost,
  acceptInviteExistingUserApiV1TenantsInvitesAcceptCurrentPost,
  issueInviteApiV1TenantsInvitesPost,
  listInvitesApiV1TenantsInvitesGet,
  listMembersApiV1TenantsMembersGet,
  removeMemberApiV1TenantsMembersUserIdDelete,
  revokeInviteApiV1TenantsInvitesInviteIdRevokePost,
  updateMemberRoleApiV1TenantsMembersUserIdRolePatch,
} from '@/lib/api/client/sdk.gen';
import type {
  SuccessNoDataResponse,
  TeamInviteAcceptExistingRequest,
  TeamInviteAcceptRequest,
  TeamInviteIssueRequest,
  TeamInviteIssueResponse,
  TeamInviteListResponse,
  TeamInviteResponse,
  TeamMemberAddRequest,
  TeamMemberListResponse,
  TeamMemberResponse,
  TeamMemberRoleUpdateRequest,
  UserSessionResponse,
} from '@/lib/api/client/types.gen';
import type {
  AddTeamMemberInput,
  TeamInviteAcceptInput,
  TeamInviteIssueResult,
  TeamInviteListFilters,
  TeamInviteListResult,
  TeamInviteSummary,
  IssueTeamInviteInput,
  TeamMemberListFilters,
  TeamMemberListResult,
  TeamMemberSummary,
  UpdateTeamMemberRoleInput,
} from '@/types/team';

import { createApiClient, getServerApiClient } from '../apiClient';

export class TeamServiceError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'TeamServiceError';
  }
}

type SdkFieldsResult<T> =
  | {
      data: T;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

const DEFAULT_LIMIT = 50;
const MAX_LIMIT = 200;

function clampLimit(value: number | undefined): number {
  if (!value || Number.isNaN(value)) return DEFAULT_LIMIT;
  if (value <= 0) return DEFAULT_LIMIT;
  return Math.min(value, MAX_LIMIT);
}

function clampOffset(value: number | undefined): number {
  if (!value || Number.isNaN(value) || value < 0) return 0;
  return value;
}

function mapErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }
  const record = payload as Record<string, unknown>;
  if (Array.isArray(record.detail)) {
    for (const entry of record.detail) {
      if (typeof entry === 'string') return entry;
      if (entry && typeof entry === 'object') {
        const entryRecord = entry as Record<string, unknown>;
        if (typeof entryRecord.msg === 'string') return entryRecord.msg;
        if (typeof entryRecord.message === 'string') return entryRecord.message;
      }
    }
  }
  if (typeof record.detail === 'string') return record.detail;
  if (typeof record.message === 'string') return record.message;
  if (typeof record.error === 'string') return record.error;
  return fallback;
}

function unwrapSdkResult<T>(result: SdkFieldsResult<T>, fallbackMessage: string): T {
  if (result.error) {
    throw new TeamServiceError(result.response.status, mapErrorMessage(result.error, fallbackMessage));
  }
  if (!result.data) {
    throw new TeamServiceError(result.response.status ?? 500, fallbackMessage);
  }
  return result.data;
}

function mapMember(dto: TeamMemberResponse): TeamMemberSummary {
  return {
    userId: dto.user_id,
    tenantId: dto.tenant_id,
    email: dto.email,
    displayName: dto.display_name ?? null,
    role: dto.role,
    status: dto.status,
    emailVerified: dto.email_verified,
    joinedAt: dto.joined_at,
  };
}

function mapInvite(dto: TeamInviteResponse): TeamInviteSummary {
  return {
    id: dto.id,
    tenantId: dto.tenant_id,
    tokenHint: dto.token_hint,
    invitedEmail: dto.invited_email,
    role: dto.role,
    status: dto.status as TeamInviteSummary['status'],
    createdByUserId: dto.created_by_user_id ?? null,
    acceptedByUserId: dto.accepted_by_user_id ?? null,
    acceptedAt: dto.accepted_at ?? null,
    revokedAt: dto.revoked_at ?? null,
    revokedReason: dto.revoked_reason ?? null,
    expiresAt: dto.expires_at ?? null,
    createdAt: dto.created_at,
  };
}

function mapInviteIssue(dto: TeamInviteIssueResponse): TeamInviteIssueResult {
  return {
    invite: mapInvite(dto),
    inviteToken: dto.invite_token,
  };
}

export async function listTeamMembers(
  filters: TeamMemberListFilters = {},
): Promise<TeamMemberListResult> {
  const limit = clampLimit(filters.limit);
  const offset = clampOffset(filters.offset);

  const { client, auth } = await getServerApiClient();
  const result = await listMembersApiV1TenantsMembersGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    query: {
      limit,
      offset,
    },
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<TeamMemberListResponse>,
    'Unable to load team members.',
  );

  return {
    members: payload.members.map(mapMember),
    total: payload.total,
    limit,
    offset,
  };
}

export async function addTeamMember(
  payload: AddTeamMemberInput,
): Promise<TeamMemberSummary> {
  const { client, auth } = await getServerApiClient();
  const body: TeamMemberAddRequest = {
    email: payload.email,
    role: payload.role,
  };

  const result = await addMemberApiV1TenantsMembersPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });

  const member = unwrapSdkResult(
    result as SdkFieldsResult<TeamMemberResponse>,
    'Unable to add team member.',
  );

  return mapMember(member);
}

export async function updateTeamMemberRole(
  userId: string,
  payload: UpdateTeamMemberRoleInput,
): Promise<TeamMemberSummary> {
  const { client, auth } = await getServerApiClient();
  const body: TeamMemberRoleUpdateRequest = {
    role: payload.role,
  };

  const result = await updateMemberRoleApiV1TenantsMembersUserIdRolePatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    path: {
      user_id: userId,
    },
    body,
  });

  const member = unwrapSdkResult(
    result as SdkFieldsResult<TeamMemberResponse>,
    'Unable to update team member role.',
  );

  return mapMember(member);
}

export async function removeTeamMember(userId: string): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const result = await removeMemberApiV1TenantsMembersUserIdDelete({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: {
      user_id: userId,
    },
  });

  return unwrapSdkResult(
    result as SdkFieldsResult<SuccessNoDataResponse>,
    'Unable to remove team member.',
  );
}

export async function listTeamInvites(
  filters: TeamInviteListFilters = {},
): Promise<TeamInviteListResult> {
  const limit = clampLimit(filters.limit);
  const offset = clampOffset(filters.offset);
  const email = filters.email?.trim() ? filters.email.trim() : undefined;

  const { client, auth } = await getServerApiClient();
  const result = await listInvitesApiV1TenantsInvitesGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    query: {
      status: filters.status ?? undefined,
      email,
      limit,
      offset,
    },
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<TeamInviteListResponse>,
    'Unable to load team invites.',
  );

  return {
    invites: payload.invites.map(mapInvite),
    total: payload.total,
    limit,
    offset,
  };
}

export async function issueTeamInvite(
  payload: IssueTeamInviteInput,
): Promise<TeamInviteIssueResult> {
  const { client, auth } = await getServerApiClient();
  const body: TeamInviteIssueRequest = {
    invited_email: payload.invitedEmail,
    role: payload.role,
    expires_in_hours: payload.expiresInHours ?? undefined,
  };

  const result = await issueInviteApiV1TenantsInvitesPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });

  const invite = unwrapSdkResult(
    result as SdkFieldsResult<TeamInviteIssueResponse>,
    'Unable to issue team invite.',
  );

  return mapInviteIssue(invite);
}

export async function revokeTeamInvite(inviteId: string): Promise<TeamInviteSummary> {
  const { client, auth } = await getServerApiClient();
  const result = await revokeInviteApiV1TenantsInvitesInviteIdRevokePost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: {
      invite_id: inviteId,
    },
  });

  const invite = unwrapSdkResult(
    result as SdkFieldsResult<TeamInviteResponse>,
    'Unable to revoke team invite.',
  );

  return mapInvite(invite);
}

export async function acceptTeamInvite(
  payload: TeamInviteAcceptInput,
): Promise<UserSessionResponse> {
  const client = createApiClient();
  const body: TeamInviteAcceptRequest = {
    token: payload.token,
    password: payload.password,
    display_name: payload.displayName ?? undefined,
  };

  const result = await acceptInviteApiV1TenantsInvitesAcceptPost({
    client,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });

  return unwrapSdkResult(
    result as SdkFieldsResult<UserSessionResponse>,
    'Unable to accept team invite.',
  );
}

export async function acceptTeamInviteExisting(
  payload: { token: string },
): Promise<TeamInviteSummary> {
  const { client, auth } = await getServerApiClient();
  const body: TeamInviteAcceptExistingRequest = {
    token: payload.token,
  };

  const result = await acceptInviteExistingUserApiV1TenantsInvitesAcceptCurrentPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });

  const invite = unwrapSdkResult(
    result as SdkFieldsResult<TeamInviteResponse>,
    'Unable to accept team invite.',
  );

  return mapInvite(invite);
}
