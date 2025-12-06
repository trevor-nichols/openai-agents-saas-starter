import type {
  ApproveSignupRequestInput,
  IssueSignupInviteInput,
  RejectSignupRequestInput,
  SignupAccessPolicy,
  SignupAccessRequestInput,
  SignupInviteIssueResult,
  SignupInviteListFilters,
  SignupInviteListResult,
  SignupInviteSummary,
  SignupRequestDecisionResult,
  SignupRequestListFilters,
  SignupRequestListResult,
} from '@/types/signup';
import { apiV1Path } from '@/lib/apiPaths';

interface ApiResponse<TData> {
  success: boolean;
  data?: TData;
  error?: string;
}

interface ListResponse<TItem> {
  success: boolean;
  error?: string;
  total?: number;
  limit?: number;
  offset?: number;
  invites?: TItem[];
  requests?: TItem[];
}

interface PolicyResponse {
  success: boolean;
  policy?: SignupAccessPolicy;
  error?: string;
}

interface AccessRequestResponse {
  success: boolean;
  policy?: SignupAccessPolicy;
  error?: string;
}

export async function fetchSignupPolicy(): Promise<SignupAccessPolicy> {
  const response = await fetch(apiV1Path('/auth/signup-policy'), { method: 'GET', cache: 'no-store' });
  const payload = (await response.json()) as PolicyResponse;

  if (!response.ok || payload.success === false || !payload.policy) {
    throw new Error(payload.error || 'Failed to load signup policy.');
  }

  return payload.policy;
}

export async function fetchSignupInvites(
  filters: SignupInviteListFilters = {},
): Promise<SignupInviteListResult> {
  const search = new URLSearchParams();
  if (filters.status) {
    search.set('status', filters.status);
  }
  if (filters.email) {
    search.set('email', filters.email);
  }
  if (filters.requestId) {
    search.set('request_id', filters.requestId);
  }
  if (typeof filters.limit === 'number') {
    search.set('limit', String(filters.limit));
  }
  if (typeof filters.offset === 'number') {
    search.set('offset', String(filters.offset));
  }

  const response = await fetch(
    apiV1Path(`/auth/invites${search.size > 0 ? `?${search.toString()}` : ''}`),
    {
      method: 'GET',
      cache: 'no-store',
    },
  );

  const payload = (await response.json()) as ListResponse<SignupInviteSummary>;

  if (!response.ok || payload.success === false || !Array.isArray(payload.invites)) {
    throw new Error(payload.error || 'Failed to load signup invites.');
  }

  return {
    invites: payload.invites,
    total: payload.total ?? payload.invites.length,
    limit: payload.limit ?? filters.limit ?? payload.invites.length,
    offset: payload.offset ?? filters.offset ?? 0,
  };
}

export async function issueSignupInviteRequest(
  payload: IssueSignupInviteInput,
): Promise<SignupInviteIssueResult> {
  const response = await fetch(apiV1Path('/auth/invites'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const result = (await response.json()) as ApiResponse<SignupInviteIssueResult>;

  if (!response.ok || result.success === false || !result.data) {
    throw new Error(result.error || 'Failed to issue signup invite.');
  }

  return result.data;
}

export async function revokeSignupInviteRequest(inviteId: string): Promise<SignupInviteSummary> {
  if (!inviteId) {
    throw new Error('Invite id is required.');
  }

  const response = await fetch(apiV1Path(`/auth/invites/${encodeURIComponent(inviteId)}/revoke`), {
    method: 'POST',
    cache: 'no-store',
  });

  const result = (await response.json()) as ApiResponse<SignupInviteSummary>;

  if (!response.ok || result.success === false || !result.data) {
    throw new Error(result.error || 'Failed to revoke signup invite.');
  }

  return result.data;
}

export async function fetchSignupRequests(
  filters: SignupRequestListFilters = {},
): Promise<SignupRequestListResult> {
  const search = new URLSearchParams();
  if (filters.status) {
    search.set('status', filters.status);
  }
  if (typeof filters.limit === 'number') {
    search.set('limit', String(filters.limit));
  }
  if (typeof filters.offset === 'number') {
    search.set('offset', String(filters.offset));
  }

  const response = await fetch(
    apiV1Path(`/auth/signup-requests${search.size > 0 ? `?${search.toString()}` : ''}`),
    {
      method: 'GET',
      cache: 'no-store',
    },
  );

  const payload = (await response.json()) as ListResponse<SignupRequestListResult['requests'][number]>;

  if (!response.ok || payload.success === false || !Array.isArray(payload.requests)) {
    throw new Error(payload.error || 'Failed to load signup requests.');
  }

  return {
    requests: payload.requests,
    total: payload.total ?? payload.requests.length,
    limit: payload.limit ?? filters.limit ?? payload.requests.length,
    offset: payload.offset ?? filters.offset ?? 0,
  };
}

export async function approveSignupRequestAction(
  requestId: string,
  payload: ApproveSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  if (!requestId) {
    throw new Error('Request id is required.');
  }

  const response = await fetch(
    apiV1Path(`/auth/signup-requests/${encodeURIComponent(requestId)}/approve`),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    },
  );

  const result = (await response.json()) as ApiResponse<SignupRequestDecisionResult>;

  if (!response.ok || result.success === false || !result.data) {
    throw new Error(result.error || 'Failed to approve signup request.');
  }

  return result.data;
}

export async function rejectSignupRequestAction(
  requestId: string,
  payload: RejectSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  if (!requestId) {
    throw new Error('Request id is required.');
  }

  const response = await fetch(
    apiV1Path(`/auth/signup-requests/${encodeURIComponent(requestId)}/reject`),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    },
  );

  const result = (await response.json()) as ApiResponse<SignupRequestDecisionResult>;

  if (!response.ok || result.success === false || !result.data) {
    throw new Error(result.error || 'Failed to reject signup request.');
  }

  return result.data;
}

export async function submitSignupAccessRequest(
  payload: SignupAccessRequestInput,
): Promise<SignupAccessPolicy> {
  const response = await fetch(apiV1Path('/auth/request-access'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const result = (await response.json()) as AccessRequestResponse;

  if (!response.ok || result.success === false || !result.policy) {
    throw new Error(result.error || 'Failed to submit access request.');
  }

  return result.policy;
}
