import type {
  TeamInviteIssueResponse,
  TeamInviteResponse,
  TeamInviteStatus,
  TeamMemberResponse,
  TenantRole,
} from '@/lib/api/client/types.gen';

export type TeamRole = TenantRole;

export const TEAM_ROLE_ORDER: readonly TeamRole[] = [
  'viewer',
  'member',
  'admin',
  'owner',
];

export type TeamInviteStatusFilter = TeamInviteStatus;
export type TeamMemberStatus = TeamMemberResponse['status'];

export interface TeamMemberSummary {
  userId: string;
  tenantId: string;
  email: string;
  displayName: string | null;
  role: TeamRole;
  status: TeamMemberStatus;
  emailVerified: boolean;
  joinedAt: string;
}

export interface TeamMemberListFilters {
  limit?: number;
  offset?: number;
}

export interface TeamMemberListResult {
  members: TeamMemberSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface AddTeamMemberInput {
  email: string;
  role: TeamRole;
}

export interface UpdateTeamMemberRoleInput {
  role: TeamRole;
}

export interface TeamInviteSummary {
  id: string;
  tenantId: string;
  tokenHint: string;
  invitedEmail: string;
  role: TeamRole;
  status: TeamInviteStatus;
  createdByUserId: string | null;
  acceptedByUserId: string | null;
  acceptedAt: string | null;
  revokedAt: string | null;
  revokedReason: string | null;
  expiresAt: string | null;
  createdAt: string;
}

export interface TeamInviteListFilters {
  status?: TeamInviteStatusFilter | null;
  email?: string | null;
  limit?: number;
  offset?: number;
}

export interface TeamInviteListResult {
  invites: TeamInviteSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface IssueTeamInviteInput {
  invitedEmail: string;
  role: TeamRole;
  expiresInHours?: number | null;
}

export interface TeamInviteIssueResult {
  invite: TeamInviteSummary;
  inviteToken: string;
}

export interface TeamInviteAcceptInput {
  token: string;
  password: string;
  displayName?: string | null;
}

export type TeamInviteDto = TeamInviteResponse | TeamInviteIssueResponse;
