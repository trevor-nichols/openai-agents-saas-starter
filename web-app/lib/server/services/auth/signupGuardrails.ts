'use server';

import {
  approveSignupRequestApiV1AuthSignupRequestsRequestIdApprovePost,
  getSignupAccessPolicyApiV1AuthSignupPolicyGet,
  issueInviteApiV1AuthInvitesPost,
  listInvitesApiV1AuthInvitesGet,
  listSignupRequestsApiV1AuthSignupRequestsGet,
  rejectSignupRequestApiV1AuthSignupRequestsRequestIdRejectPost,
  revokeInviteApiV1AuthInvitesInviteIdRevokePost,
  submitAccessRequestApiV1AuthRequestAccessPost,
} from '@/lib/api/client/sdk.gen';
import type {
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
} from '@/lib/api/client/types.gen';

import { createApiClient, getServerApiClient } from '../../apiClient';
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
  SignupRequestSummary,
} from '@/types/signup';

export class SignupGuardrailServiceError extends Error {
  status: number;

  constructor(message: string, status = 500) {
    super(message);
    this.name = 'SignupGuardrailServiceError';
    this.status = status;
  }
}

const DEFAULT_INVITE_LIMIT = 25;
const DEFAULT_REQUEST_LIMIT = 25;
const MAX_LIMIT = 200;

export async function getSignupAccessPolicy(): Promise<SignupAccessPolicy> {
  const client = createApiClient();
  try {
    const response = await getSignupAccessPolicyApiV1AuthSignupPolicyGet({
      client,
      responseStyle: 'fields',
      throwOnError: true,
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Signup policy response was empty.');
    }

    return response.data;
  } catch (error) {
    throw normalizeError(error, 'Unable to load signup policy.');
  }
}

export async function submitSignupAccessRequest(
  payload: SignupAccessRequestInput,
): Promise<SignupAccessPolicy> {
  const client = createApiClient();
  const body: SignupRequestPublicRequest = {
    email: payload.email,
    organization: payload.organization,
    full_name: payload.fullName,
    message: normalizeString(payload.message) ?? undefined,
    accept_terms: payload.acceptTerms,
    honeypot: normalizeString(payload.honeypot) ?? undefined,
  };

  try {
    const response = await submitAccessRequestApiV1AuthRequestAccessPost({
      client,
      responseStyle: 'fields',
      throwOnError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body,
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Access-request response was empty.');
    }

    return response.data;
  } catch (error) {
    throw normalizeError(error, 'Unable to submit access request.');
  }
}

export async function listSignupInvites(
  filters: SignupInviteListFilters = {},
): Promise<SignupInviteListResult> {
  const limit = clampLimit(filters.limit ?? DEFAULT_INVITE_LIMIT, DEFAULT_INVITE_LIMIT);
  const offset = clampOffset(filters.offset ?? 0);

  const { client, auth } = await getServerApiClient();

  try {
    const response = await listInvitesApiV1AuthInvitesGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        status: filters.status ?? undefined,
        email: normalizeString(filters.email),
        request_id: normalizeString(filters.requestId),
        limit,
        offset,
      },
    });

    const payload = response.data;
    if (!payload) {
      throw new SignupGuardrailServiceError('Invite list response was empty.');
    }

    return mapInviteListResponse(payload, limit, offset);
  } catch (error) {
    throw normalizeError(error, 'Unable to load signup invites.');
  }
}

export async function issueSignupInvite(payload: IssueSignupInviteInput): Promise<SignupInviteIssueResult> {
  const body: SignupInviteIssueRequest = {
    invited_email: normalizeString(payload.invitedEmail) ?? undefined,
    max_redemptions: payload.maxRedemptions,
    expires_in_hours: payload.expiresInHours ?? undefined,
    note: normalizeString(payload.note),
    signup_request_id: normalizeString(payload.signupRequestId),
  };

  const { client, auth } = await getServerApiClient();

  try {
    const response = await issueInviteApiV1AuthInvitesPost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      body,
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Issue-invite response was empty.');
    }

    return mapInviteIssueResponse(response.data);
  } catch (error) {
    throw normalizeError(error, 'Unable to issue signup invite.');
  }
}

export async function revokeSignupInvite(inviteId: string): Promise<SignupInviteSummary> {
  if (!inviteId) {
    throw new SignupGuardrailServiceError('Invite id is required.', 400);
  }

  const { client, auth } = await getServerApiClient();

  try {
    const response = await revokeInviteApiV1AuthInvitesInviteIdRevokePost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      path: {
        invite_id: inviteId,
      },
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Revoke-invite response was empty.');
    }

    return mapInvite(response.data);
  } catch (error) {
    throw normalizeError(error, 'Unable to revoke signup invite.');
  }
}

export async function listSignupRequests(
  filters: SignupRequestListFilters = {},
): Promise<SignupRequestListResult> {
  const limit = clampLimit(filters.limit ?? DEFAULT_REQUEST_LIMIT, DEFAULT_REQUEST_LIMIT);
  const offset = clampOffset(filters.offset ?? 0);

  const { client, auth } = await getServerApiClient();

  try {
    const response = await listSignupRequestsApiV1AuthSignupRequestsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        status: filters.status ?? undefined,
        limit,
        offset,
      },
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Signup request list response was empty.');
    }

    return mapRequestListResponse(response.data, limit, offset);
  } catch (error) {
    throw normalizeError(error, 'Unable to load signup requests.');
  }
}

export async function approveSignupRequest(
  requestId: string,
  payload: ApproveSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  if (!requestId) {
    throw new SignupGuardrailServiceError('Request id is required.', 400);
  }

  const body: SignupRequestApprovalRequest = {
    note: normalizeString(payload.note),
    invite_expires_in_hours: payload.inviteExpiresInHours ?? undefined,
  };

  const { client, auth } = await getServerApiClient();

  try {
    const response = await approveSignupRequestApiV1AuthSignupRequestsRequestIdApprovePost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      path: {
        request_id: requestId,
      },
      body,
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Approve-request response was empty.');
    }

    return mapRequestDecisionResponse(response.data);
  } catch (error) {
    throw normalizeError(error, 'Unable to approve signup request.');
  }
}

export async function rejectSignupRequest(
  requestId: string,
  payload: RejectSignupRequestInput,
): Promise<SignupRequestDecisionResult> {
  if (!requestId) {
    throw new SignupGuardrailServiceError('Request id is required.', 400);
  }

  const body: SignupRequestRejectionRequest = {
    reason: normalizeString(payload.reason),
  };

  const { client, auth } = await getServerApiClient();

  try {
    const response = await rejectSignupRequestApiV1AuthSignupRequestsRequestIdRejectPost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      headers: {
        'Content-Type': 'application/json',
      },
      path: {
        request_id: requestId,
      },
      body,
    });

    if (!response.data) {
      throw new SignupGuardrailServiceError('Reject-request response was empty.');
    }

    return mapRequestDecisionResponse(response.data);
  } catch (error) {
    throw normalizeError(error, 'Unable to reject signup request.');
  }
}

function mapInviteListResponse(
  payload: SignupInviteListResponse,
  limit: number,
  offset: number,
): SignupInviteListResult {
  return {
    invites: payload.invites?.map(mapInvite) ?? [],
    total: payload.total ?? 0,
    limit,
    offset,
  };
}

function mapInvite(payload: SignupInviteResponse): SignupInviteSummary {
  return {
    id: payload.id,
    tokenHint: payload.token_hint,
    invitedEmail: payload.invited_email ?? null,
    status: payload.status as SignupInviteSummary['status'],
    maxRedemptions: payload.max_redemptions,
    redeemedCount: payload.redeemed_count,
    expiresAt: payload.expires_at ?? null,
    createdAt: payload.created_at,
    signupRequestId: payload.signup_request_id ?? null,
    note: payload.note ?? null,
  };
}

function mapInviteIssueResponse(payload: SignupInviteIssueResponse): SignupInviteIssueResult {
  return {
    invite: mapInvite(payload),
    inviteToken: payload.invite_token,
  };
}

function mapRequestListResponse(
  payload: SignupRequestListResponse,
  limit: number,
  offset: number,
): SignupRequestListResult {
  return {
    requests: payload.requests?.map(mapRequest) ?? [],
    total: payload.total ?? 0,
    limit,
    offset,
  };
}

function mapRequestDecisionResponse(payload: SignupRequestDecisionResponse): SignupRequestDecisionResult {
  return {
    request: mapRequest(payload.request),
    invite: payload.invite ? mapInviteIssueResponse(payload.invite) : null,
  };
}

function mapRequest(payload: SignupRequestResponse): SignupRequestSummary {
  return {
    id: payload.id,
    email: payload.email,
    organization: payload.organization ?? null,
    fullName: payload.full_name ?? null,
    status: payload.status as SignupRequestSummary['status'],
    createdAt: payload.created_at,
    decisionReason: payload.decision_reason ?? null,
    inviteTokenHint: payload.invite_token_hint ?? null,
  };
}

function clampLimit(value: number, fallback: number): number {
  if (!Number.isFinite(value) || value <= 0) {
    return fallback;
  }
  return Math.min(Math.trunc(value), MAX_LIMIT);
}

function clampOffset(value: number): number {
  if (!Number.isFinite(value) || value < 0) {
    return 0;
  }
  return Math.trunc(value);
}

function normalizeString(value: string | null | undefined): string | null {
  if (typeof value !== 'string') {
    return null;
  }
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function normalizeError(error: unknown, fallbackMessage: string): SignupGuardrailServiceError {
  if (error instanceof SignupGuardrailServiceError) {
    return error;
  }

  const message = error instanceof Error ? error.message : fallbackMessage;
  const status = mapErrorToStatus(message);
  return new SignupGuardrailServiceError(message || fallbackMessage, status);
}

function mapErrorToStatus(message: string): number {
  const normalized = (message ?? '').toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('forbidden') || normalized.includes('permission')) {
    return 403;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  if (normalized.includes('rate limit')) {
    return 429;
  }
  if (normalized.includes('validation')) {
    return 422;
  }
  return 500;
}
