'use server';

import {
  billingEventStreamApiV1BillingStreamGet,
  cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost,
  getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet,
  listBillingEventsApiV1BillingTenantsTenantIdEventsGet,
  listBillingPlansApiV1BillingPlansGet,
  recordUsageApiV1BillingTenantsTenantIdUsagePost,
  startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost,
  updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch,
} from '@/lib/api/client/sdk.gen';
import type {
  BillingPlanResponse,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  CancelSubscriptionRequest,
  UsageRecordRequest,
  StripeEventStatus,
} from '@/lib/api/client/types.gen';
import type { BillingEventHistoryResponse } from '@/types/billing';

import { USE_API_MOCK } from '@/lib/config';

import { getServerApiClient } from '../apiClient';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

function assertBillingSdkPresent() {
  const missing: string[] = [];
  if (!billingEventStreamApiV1BillingStreamGet) missing.push('billingEventStreamApiV1BillingStreamGet');
  if (!listBillingPlansApiV1BillingPlansGet) missing.push('listBillingPlansApiV1BillingPlansGet');
  if (!listBillingEventsApiV1BillingTenantsTenantIdEventsGet) {
    missing.push('listBillingEventsApiV1BillingTenantsTenantIdEventsGet');
  }
  if (!getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet) {
    missing.push('getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet');
  }
  if (!startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost) {
    missing.push('startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost');
  }
  if (!updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch) {
    missing.push('updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch');
  }
  if (!cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost) {
    missing.push('cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost');
  }
  if (!recordUsageApiV1BillingTenantsTenantIdUsagePost) {
    missing.push('recordUsageApiV1BillingTenantsTenantIdUsagePost');
  }

  if (missing.length) {
    throw new Error(
      `Billing SDK exports missing: ${missing.join(
        ', ',
      )}. Regenerate via "pnpm generate" against api-service/.artifacts/openapi-billing.json.`,
    );
  }
}

assertBillingSdkPresent();

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

  const headers = new Headers({
    Accept: 'text/event-stream',
    ...(options.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
  });

  const upstream = await billingEventStreamApiV1BillingStreamGet({
    client,
    auth,
    signal: options.signal,
    cache: 'no-store',
    headers,
    parseAs: 'stream',
    responseStyle: 'fields',
    throwOnError: true,
  });

  const stream = upstream.data;

  if (!stream || !upstream.response) {
    throw new Error('Billing stream returned no data.');
  }

  const responseHeaders = new Headers(STREAM_HEADERS);
  const contentType = upstream.response.headers.get('Content-Type');
  if (contentType) {
    responseHeaders.set('Content-Type', contentType);
  }

  return new Response(stream as BodyInit, {
    status: upstream.response.status,
    statusText: upstream.response.statusText,
    headers: responseHeaders,
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
