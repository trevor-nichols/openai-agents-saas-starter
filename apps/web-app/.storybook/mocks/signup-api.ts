import type {
  ApproveSignupRequestInput,
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
  SignupRequestSummary,
} from '@/types/signup';

const now = Date.now();

let policy: SignupAccessPolicy = {
  policy: 'invite_only',
  invite_required: true,
  request_access_enabled: true,
};

let invites: SignupInviteSummary[] = [
  {
    id: 'invite-1',
    tokenHint: 'abcd-1234',
    invitedEmail: 'ops@example.com',
    status: 'active',
    maxRedemptions: 3,
    redeemedCount: 1,
    expiresAt: new Date(now + 72 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
    signupRequestId: 'req-1',
    note: 'VIP prospect',
  },
  {
    id: 'invite-2',
    tokenHint: 'efgh-5678',
    invitedEmail: null,
    status: 'revoked',
    maxRedemptions: 5,
    redeemedCount: 2,
    expiresAt: new Date(now - 24 * 60 * 60 * 1000).toISOString(),
    createdAt: new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString(),
    signupRequestId: null,
    note: null,
  },
];

let requests: SignupRequestSummary[] = [
  {
    id: 'req-1',
    email: 'amy@acme.com',
    organization: 'Acme Co',
    fullName: 'Amy Lee',
    status: 'pending',
    createdAt: new Date(now - 4 * 60 * 60 * 1000).toISOString(),
    decisionReason: null,
    inviteTokenHint: null,
  },
  {
    id: 'req-2',
    email: 'bob@startup.io',
    organization: 'Startup.io',
    fullName: 'Bob Smith',
    status: 'approved',
    createdAt: new Date(now - 2 * 24 * 60 * 60 * 1000).toISOString(),
    decisionReason: 'Invited with 7-day expiry',
    inviteTokenHint: 'xyza-0001',
  },
  {
    id: 'req-3',
    email: 'carla@example.org',
    organization: null,
    fullName: 'Carla Fernandez',
    status: 'rejected',
    createdAt: new Date(now - 5 * 24 * 60 * 60 * 1000).toISOString(),
    decisionReason: 'Missing business justification',
    inviteTokenHint: null,
  },
];

export async function fetchSignupPolicy(): Promise<SignupAccessPolicy> {
  return policy;
}

export async function fetchSignupInvites(filters: SignupInviteListFilters = {}): Promise<SignupInviteListResult> {
  const filtered = invites.filter((invite) => {
    if (filters.status && invite.status !== filters.status) return false;
    if (filters.email && invite.invitedEmail && !invite.invitedEmail.includes(filters.email)) return false;
    if (filters.requestId && invite.signupRequestId !== filters.requestId) return false;
    return true;
  });
  const limit = filters.limit ?? 25;
  const offset = filters.offset ?? 0;
  return {
    invites: filtered.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

export async function fetchSignupRequests(filters: SignupRequestListFilters = {}): Promise<SignupRequestListResult> {
  const filtered = requests.filter((request) => {
    if (filters.status && request.status !== filters.status) return false;
    return true;
  });
  const limit = filters.limit ?? 25;
  const offset = filters.offset ?? 0;
  return {
    requests: filtered.slice(offset, offset + limit),
    total: filtered.length,
    limit,
    offset,
  };
}

export async function issueSignupInviteRequest(payload: IssueSignupInviteInput): Promise<SignupInviteIssueResult> {
  const invite: SignupInviteSummary = {
    id: `invite-${invites.length + 1}`,
    tokenHint: `token-${invites.length + 1}`,
    invitedEmail: payload.invitedEmail ?? null,
    status: 'active',
    maxRedemptions: payload.maxRedemptions ?? 1,
    redeemedCount: 0,
    expiresAt: payload.expiresInHours
      ? new Date(Date.now() + payload.expiresInHours * 60 * 60 * 1000).toISOString()
      : null,
    createdAt: new Date().toISOString(),
    signupRequestId: payload.signupRequestId ?? null,
    note: payload.note ?? null,
  };
  invites = [invite, ...invites];
  return { invite, inviteToken: `${invite.tokenHint}-full-token` };
}

export async function revokeSignupInviteRequest(inviteId: string): Promise<SignupInviteSummary> {
  invites = invites.map((invite) => (invite.id === inviteId ? { ...invite, status: 'revoked' } : invite));
  const updated = invites.find((invite) => invite.id === inviteId);
  if (!updated) {
    throw new Error('Invite not found');
  }
  return updated;
}

export async function approveSignupRequestAction(
  requestId: string,
  payload: ApproveSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  const target = requests.find((req) => req.id === requestId);
  if (!target) throw new Error('Request not found');
  const invite = (await issueSignupInviteRequest({
    invitedEmail: target.email,
    expiresInHours: payload.inviteExpiresInHours ?? undefined,
    note: payload.note ?? undefined,
    signupRequestId: target.id,
  })) as SignupInviteIssueResult;
  requests = requests.map((req) =>
    req.id === requestId
      ? { ...req, status: 'approved', decisionReason: payload.note ?? null, inviteTokenHint: invite.invite.tokenHint }
      : req,
  );
  return {
    request: requests.find((req) => req.id === requestId) as SignupRequestSummary,
    invite,
  };
}

export async function rejectSignupRequestAction(
  requestId: string,
  payload: RejectSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  const target = requests.find((req) => req.id === requestId);
  if (!target) throw new Error('Request not found');
  requests = requests.map((req) =>
    req.id === requestId ? { ...req, status: 'rejected', decisionReason: payload.reason ?? null } : req,
  );
  return {
    request: requests.find((req) => req.id === requestId) as SignupRequestSummary,
    invite: null,
  };
}

export async function submitSignupAccessRequest(): Promise<SignupAccessPolicy> {
  return policy;
}
