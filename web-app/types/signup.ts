import type {
  SignupAccessPolicyResponse,
  SignupInviteIssueRequest,
  SignupInviteIssueResponse,
  SignupInviteListResponse,
  SignupInviteResponse,
  SignupInviteStatus,
  SignupRequestApprovalRequest,
  SignupRequestDecisionResponse,
  SignupRequestListResponse,
  SignupRequestPublicRequest,
  SignupRequestRejectionRequest,
  SignupRequestResponse,
  SignupRequestStatus,
} from '@/lib/api/client/types.gen';

export type SignupAccessPolicy = SignupAccessPolicyResponse;
export type SignupAccessPolicyMode = 'public' | 'invite_only' | 'approval';

export function resolveSignupPolicyMode(policy?: SignupAccessPolicy | null): SignupAccessPolicyMode {
  const value = policy?.policy;
  if (value === 'invite_only' || value === 'approval') {
    return value;
  }
  return 'public';
}

export type SignupInviteStatusFilter = SignupInviteStatus;

export interface SignupInviteSummary {
  id: string;
  tokenHint: string;
  invitedEmail: string | null;
  status: SignupInviteStatus;
  maxRedemptions: number;
  redeemedCount: number;
  expiresAt: string | null;
  createdAt: string;
  signupRequestId: string | null;
  note: string | null;
}

export interface SignupInviteListResult {
  invites: SignupInviteSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface SignupInviteListFilters {
  status?: SignupInviteStatusFilter | null;
  email?: string | null;
  requestId?: string | null;
  limit?: number;
  offset?: number;
}

export interface IssueSignupInviteInput {
  invitedEmail?: string | null;
  maxRedemptions?: number;
  expiresInHours?: number | null;
  note?: string | null;
  signupRequestId?: string | null;
}

export interface SignupInviteIssueResult {
  invite: SignupInviteSummary;
  inviteToken: string;
}

export type SignupRequestStatusFilter = SignupRequestStatus;

export interface SignupRequestSummary {
  id: string;
  email: string;
  organization: string | null;
  fullName: string | null;
  status: SignupRequestStatus;
  createdAt: string;
  decisionReason: string | null;
  inviteTokenHint: string | null;
}

export interface SignupRequestListFilters {
  status?: SignupRequestStatusFilter | null;
  limit?: number;
  offset?: number;
}

export interface SignupRequestListResult {
  requests: SignupRequestSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface ApproveSignupRequestInput {
  note?: string | null;
  inviteExpiresInHours?: number | null;
}

export interface RejectSignupRequestInput {
  reason?: string | null;
}

export interface SignupRequestDecisionResult {
  request: SignupRequestSummary;
  invite?: SignupInviteIssueResult | null;
}

export interface SignupAccessRequestInput {
  email: string;
  organization: string;
  fullName: string;
  message?: string | null;
  acceptTerms: boolean;
  honeypot?: string | null;
}

export type {
  SignupInviteIssueRequest,
  SignupInviteIssueResponse,
  SignupInviteListResponse,
  SignupInviteResponse,
  SignupRequestApprovalRequest,
  SignupRequestDecisionResponse,
  SignupRequestListResponse,
  SignupRequestPublicRequest,
  SignupRequestRejectionRequest,
  SignupRequestResponse,
};
