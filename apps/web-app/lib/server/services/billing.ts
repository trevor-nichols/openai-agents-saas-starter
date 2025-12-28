'use server';

import {
  cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost,
  changeSubscriptionPlanApiV1BillingTenantsTenantIdSubscriptionPlanPost,
  getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet,
  listBillingEventsApiV1BillingTenantsTenantIdEventsGet,
  listBillingPlansApiV1BillingPlansGet,
  recordUsageApiV1BillingTenantsTenantIdUsagePost,
  startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost,
  updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch,
} from '@/lib/api/client/sdk.gen';
import type {
  BillingPlanResponse,
  ChangeSubscriptionPlanRequest,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  PlanChangeResponse,
  CancelSubscriptionRequest,
  UsageRecordRequest,
  StripeEventStatus,
} from '@/lib/api/client/types.gen';
import type { BillingEventHistoryResponse } from '@/types/billing';

import { USE_API_MOCK } from '@/lib/config';

import { getServerApiClient } from '../apiClient';
import { proxyBackendSseStream } from '../streaming/sseProxy';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

export interface BillingStreamOptions {
  signal: AbortSignal;
  tenantRole?: string | null;
}

export interface ListTenantBillingEventsOptions {
  limit?: number;
  cursor?: string | null;
  eventType?: string | null;
  processingStatus?: string | null;
  tenantRole?: string | null;
}

const VALID_PROCESSING_STATUSES: StripeEventStatus[] = ['received', 'processed', 'failed'];

function normalizeProcessingStatus(status?: string | null): StripeEventStatus | undefined {
  if (!status) {
    return undefined;
  }
  return VALID_PROCESSING_STATUSES.includes(status as StripeEventStatus)
    ? (status as StripeEventStatus)
    : undefined;
}

/**
 * Connect to the billing SSE stream using the authenticated backend client.
 */
export async function openBillingStream(options: BillingStreamOptions): Promise<Response> {
  if (USE_API_MOCK) {
    return createMockBillingStream();
  }

  const { client, auth } = await getServerApiClient();

  return proxyBackendSseStream({
    client,
    auth,
    url: '/api/v1/billing/stream',
    signal: options.signal,
    requestHeaders: options.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : undefined,
    responseHeaders: STREAM_HEADERS,
  });
}

export async function listTenantBillingEvents(
  tenantId: string,
  options?: ListTenantBillingEventsOptions,
): Promise<BillingEventHistoryResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await listBillingEventsApiV1BillingTenantsTenantIdEventsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    query: {
      limit: options?.limit,
      cursor: options?.cursor ?? undefined,
      event_type: options?.eventType ?? undefined,
      processing_status: normalizeProcessingStatus(options?.processingStatus ?? undefined),
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Failed to load billing events.');
  }

  const normalized: BillingEventHistoryResponse = {
    ...payload,
    items: payload.items ?? [],
    next_cursor: payload.next_cursor ?? null,
  };

  return normalized;
}

/**
 * Fetch the catalog of billing plans for future UI use.
 */
export async function listBillingPlans(): Promise<BillingPlanResponse[]> {
  const { client, auth } = await getServerApiClient();
  const response = await listBillingPlansApiV1BillingPlansGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  return response.data ?? [];
}

export async function getTenantSubscription(
  tenantId: string,
  options?: { tenantRole?: string | null },
): Promise<TenantSubscriptionResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Subscription not found.');
  }

  return payload;
}

export async function startTenantSubscription(
  tenantId: string,
  payload: StartSubscriptionRequest,
  options?: { tenantRole?: string | null },
): Promise<TenantSubscriptionResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Subscription start returned empty payload.');
  }

  return data;
}

export async function updateTenantSubscription(
  tenantId: string,
  payload: UpdateSubscriptionRequest,
  options?: { tenantRole?: string | null },
): Promise<TenantSubscriptionResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Subscription update returned empty payload.');
  }

  return data;
}

export async function changeTenantSubscriptionPlan(
  tenantId: string,
  payload: ChangeSubscriptionPlanRequest,
  options?: { tenantRole?: string | null },
): Promise<PlanChangeResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await changeSubscriptionPlanApiV1BillingTenantsTenantIdSubscriptionPlanPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Plan change returned empty payload.');
  }

  return data;
}

export async function cancelTenantSubscription(
  tenantId: string,
  payload: CancelSubscriptionRequest,
  options?: { tenantRole?: string | null },
): Promise<TenantSubscriptionResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    body: payload,
  });

  const data = response.data;
  if (!data) {
    throw new Error('Subscription cancel returned empty payload.');
  }

  return data;
}

export async function recordTenantUsage(
  tenantId: string,
  payload: UsageRecordRequest,
  options?: { tenantRole?: string | null },
): Promise<void> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  await recordUsageApiV1BillingTenantsTenantIdUsagePost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
    },
    body: payload,
  });
}

function createMockBillingStream(): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const payload = {
        timestamp: new Date().toISOString(),
        type: 'mock.billing.event',
        description: 'Mock billing stream active.',
      };
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: STREAM_HEADERS,
  });
}
