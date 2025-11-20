'use server';

import {
  createStatusSubscriptionApiV1StatusSubscriptionsPost,
  listStatusSubscriptionsApiV1StatusSubscriptionsGet,
  resendStatusIncidentApiV1StatusIncidentsIncidentIdResendPost,
  revokeStatusSubscriptionApiV1StatusSubscriptionsSubscriptionIdDelete,
  verifyStatusSubscriptionApiV1StatusSubscriptionsVerifyPost,
} from '@/lib/api/client/sdk.gen';
import type {
  StatusIncidentResendRequest,
  StatusIncidentResendResponse,
  StatusSubscriptionCreateRequest,
  StatusSubscriptionListResponse,
  StatusSubscriptionResponse,
} from '@/lib/api/client/types.gen';

import { createApiClient, getServerApiClient } from '../apiClient';

interface ApiFieldsResult<TData> {
  data?: TData;
  error?: unknown;
  response: Response;
}

export class StatusSubscriptionServiceError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
    this.name = 'StatusSubscriptionServiceError';
  }
}

function extractErrorMessage(error: unknown, fallback: string): string {
  if (typeof error === 'string' && error.trim().length > 0) {
    return error;
  }

  if (typeof error === 'object' && error !== null) {
    const candidate = (error as Record<string, unknown>).detail
      ?? (error as Record<string, unknown>).error
      ?? (error as Record<string, unknown>).message;
    if (typeof candidate === 'string' && candidate.trim().length > 0) {
      return candidate;
    }
  }

  return fallback;
}

function assertNoError<TData>(
  result: ApiFieldsResult<TData> | undefined,
  fallbackMessage: string,
): asserts result is ApiFieldsResult<TData> {
  if (!result) {
    throw new StatusSubscriptionServiceError(fallbackMessage, 502);
  }

  if ('error' in result && result.error) {
    const message = extractErrorMessage(result.error, fallbackMessage);
    const status = result.response?.status ?? 502;
    throw new StatusSubscriptionServiceError(message, status);
  }
}

function unwrapData<TData>(
  result: ApiFieldsResult<TData> | undefined,
  fallbackMessage: string,
): TData {
  assertNoError(result, fallbackMessage);
  if (result.data === undefined) {
    const status = result.response?.status ?? 502;
    throw new StatusSubscriptionServiceError(fallbackMessage, status);
  }

  return result.data;
}

/**
 * Verify an email-based status subscription using the public token flow.
 */
export async function verifyStatusSubscriptionToken(
  token: string,
): Promise<StatusSubscriptionResponse> {
  if (!token) {
    throw new StatusSubscriptionServiceError('Verification token is required.', 400);
  }

  const client = createApiClient();
  const result = (await verifyStatusSubscriptionApiV1StatusSubscriptionsVerifyPost({
    client,
    throwOnError: false,
    responseStyle: 'fields',
    headers: {
      'Content-Type': 'application/json',
    },
    body: { token },
  })) as ApiFieldsResult<StatusSubscriptionResponse>;

  return unwrapData(result, 'Unable to verify subscription.');
}

/**
 * Unsubscribe a status subscription using the signed email token.
 */
export async function unsubscribeStatusSubscriptionViaToken(params: {
  subscriptionId: string;
  token: string;
}): Promise<void> {
  const { subscriptionId, token } = params;
  if (!subscriptionId) {
    throw new StatusSubscriptionServiceError('Subscription id is required.', 400);
  }
  if (!token) {
    throw new StatusSubscriptionServiceError('Unsubscribe token is required.', 400);
  }

  const client = createApiClient();
  const result = (await revokeStatusSubscriptionApiV1StatusSubscriptionsSubscriptionIdDelete({
    client,
    throwOnError: false,
    responseStyle: 'fields',
    path: { subscription_id: subscriptionId },
    query: { token },
  })) as ApiFieldsResult<void>;

  assertNoError(result, 'Unable to unsubscribe from alerts.');
}

type CreateSubscriptionAuthMode = 'public' | 'session';

export async function createStatusSubscription(
  payload: StatusSubscriptionCreateRequest,
  options?: { tenantRole?: string | null; authMode?: CreateSubscriptionAuthMode },
): Promise<StatusSubscriptionResponse> {
  const authMode: CreateSubscriptionAuthMode = options?.authMode ?? 'public';
  const requiresAuth = authMode === 'session' || payload.channel === 'webhook';

  const context = requiresAuth ? await getServerApiClient() : null;
  const client = context?.client ?? createApiClient();

  const result = (await createStatusSubscriptionApiV1StatusSubscriptionsPost({
    client,
    auth: context?.auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    body: payload,
  })) as ApiFieldsResult<StatusSubscriptionResponse>;

  return unwrapData(result, 'Unable to create status subscription.');
}

/**
 * Operator-facing helper to list status subscriptions (requires auth).
 */
export async function listStatusSubscriptions(options?: {
  limit?: number;
  cursor?: string | null;
  tenantId?: string | null;
  includeAllTenants?: boolean;
}): Promise<StatusSubscriptionListResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await listStatusSubscriptionsApiV1StatusSubscriptionsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: options?.limit,
      cursor: options?.cursor,
      tenant_id: options?.tenantId,
      all: options?.includeAllTenants ? true : undefined,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Status subscription list returned empty response.');
  }

  return payload;
}

/**
 * Re-dispatch a status incident notification (requires auth).
 */
export async function resendStatusIncident(
  incidentId: string,
  payload: StatusIncidentResendRequest,
): Promise<StatusIncidentResendResponse> {
  if (!incidentId) {
    throw new Error('Incident id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await resendStatusIncidentApiV1StatusIncidentsIncidentIdResendPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
    path: { incident_id: incidentId },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Status incident resend returned empty response.');
  }

  return data;
}
