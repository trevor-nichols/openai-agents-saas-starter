import 'server-only';

import {
  changeSubscriptionPlanApiV1BillingTenantsTenantIdSubscriptionPlanPost,
  cancelSubscriptionApiV1BillingTenantsTenantIdSubscriptionCancelPost,
  createPortalSessionApiV1BillingTenantsTenantIdPortalPost,
  createSetupIntentApiV1BillingTenantsTenantIdPaymentMethodsSetupIntentPost,
  detachPaymentMethodApiV1BillingTenantsTenantIdPaymentMethodsPaymentMethodIdDelete,
  getTenantSubscriptionApiV1BillingTenantsTenantIdSubscriptionGet,
  getInvoiceApiV1BillingTenantsTenantIdInvoicesInvoiceIdGet,
  listBillingEventsApiV1BillingTenantsTenantIdEventsGet,
  listBillingPlansApiV1BillingPlansGet,
  listInvoicesApiV1BillingTenantsTenantIdInvoicesGet,
  listPaymentMethodsApiV1BillingTenantsTenantIdPaymentMethodsGet,
  listUsageTotalsApiV1BillingTenantsTenantIdUsageTotalsGet,
  previewUpcomingInvoiceApiV1BillingTenantsTenantIdUpcomingInvoicePost,
  recordUsageApiV1BillingTenantsTenantIdUsagePost,
  setDefaultPaymentMethodApiV1BillingTenantsTenantIdPaymentMethodsPaymentMethodIdDefaultPost,
  startSubscriptionApiV1BillingTenantsTenantIdSubscriptionPost,
  updateSubscriptionApiV1BillingTenantsTenantIdSubscriptionPatch,
} from '@/lib/api/client/sdk.gen';
import type {
  BillingPlanResponse,
  ChangeSubscriptionPlanRequest,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  CancelSubscriptionRequest,
  UsageRecordRequest,
  StripeEventStatus,
  PortalSessionRequest,
  PortalSessionResponse,
  PaymentMethodResponse,
  SetupIntentRequest,
  SetupIntentResponse,
  SubscriptionInvoiceListResponse,
  SubscriptionInvoiceResponse,
  UpcomingInvoicePreviewRequest,
  UpcomingInvoicePreviewResponse,
  PlanChangeResponse,
  SuccessNoDataResponse,
  UsageTotalResponse,
} from '@/lib/api/client/types.gen';
import type { BillingEventHistoryResponse } from '@/types/billing';

import { USE_API_MOCK } from '@/lib/config';

import { createApiClient, getServerApiClient } from '../apiClient';
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

export interface ListTenantUsageTotalsOptions {
  featureKeys?: string[] | null;
  periodStart?: string | null;
  periodEnd?: string | null;
  tenantRole?: string | null;
}

export interface ListTenantInvoicesOptions {
  limit?: number;
  offset?: number;
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

export async function listTenantUsageTotals(
  tenantId: string,
  options?: ListTenantUsageTotalsOptions,
): Promise<UsageTotalResponse[]> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await listUsageTotalsApiV1BillingTenantsTenantIdUsageTotalsGet({
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
      feature_keys: options?.featureKeys?.length ? options.featureKeys : undefined,
      period_start: options?.periodStart ?? undefined,
      period_end: options?.periodEnd ?? undefined,
    },
  });

  return response.data ?? [];
}

export async function listTenantInvoices(
  tenantId: string,
  options?: ListTenantInvoicesOptions,
): Promise<SubscriptionInvoiceListResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await listInvoicesApiV1BillingTenantsTenantIdInvoicesGet({
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
      offset: options?.offset,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Failed to load invoices.');
  }

  return {
    ...payload,
    items: payload.items ?? [],
    next_offset: payload.next_offset ?? null,
  };
}

export async function getTenantInvoice(
  tenantId: string,
  invoiceId: string,
  options?: { tenantRole?: string | null },
): Promise<SubscriptionInvoiceResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  if (!invoiceId) {
    throw new Error('Invoice id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await getInvoiceApiV1BillingTenantsTenantIdInvoicesInvoiceIdGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
      invoice_id: invoiceId,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Invoice not found.');
  }

  return payload;
}

/**
 * Fetch the catalog of billing plans for future UI use.
 */
export async function listBillingPlans(): Promise<BillingPlanResponse[]> {
  const client = createApiClient();
  const response = await listBillingPlansApiV1BillingPlansGet({
    client,
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

export async function createTenantPortalSession(
  tenantId: string,
  payload: PortalSessionRequest,
  options?: { tenantRole?: string | null },
): Promise<PortalSessionResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await createPortalSessionApiV1BillingTenantsTenantIdPortalPost({
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
    throw new Error('Portal session returned empty payload.');
  }

  return data;
}

export async function listTenantPaymentMethods(
  tenantId: string,
  options?: { tenantRole?: string | null },
): Promise<PaymentMethodResponse[]> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await listPaymentMethodsApiV1BillingTenantsTenantIdPaymentMethodsGet({
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

  return response.data ?? [];
}

export async function createTenantSetupIntent(
  tenantId: string,
  payload: SetupIntentRequest,
  options?: { tenantRole?: string | null },
): Promise<SetupIntentResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await createSetupIntentApiV1BillingTenantsTenantIdPaymentMethodsSetupIntentPost({
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
    throw new Error('Setup intent returned empty payload.');
  }

  return data;
}

export async function setTenantDefaultPaymentMethod(
  tenantId: string,
  paymentMethodId: string,
  options?: { tenantRole?: string | null },
): Promise<SuccessNoDataResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  if (!paymentMethodId) {
    throw new Error('Payment method id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await setDefaultPaymentMethodApiV1BillingTenantsTenantIdPaymentMethodsPaymentMethodIdDefaultPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
      payment_method_id: paymentMethodId,
    },
  });

  const data = response.data;
  if (!data) {
    throw new Error('Default payment method response missing.');
  }

  return data;
}

export async function detachTenantPaymentMethod(
  tenantId: string,
  paymentMethodId: string,
  options?: { tenantRole?: string | null },
): Promise<SuccessNoDataResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  if (!paymentMethodId) {
    throw new Error('Payment method id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await detachPaymentMethodApiV1BillingTenantsTenantIdPaymentMethodsPaymentMethodIdDelete({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      ...(options?.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
    },
    path: {
      tenant_id: tenantId,
      payment_method_id: paymentMethodId,
    },
  });

  const data = response.data;
  if (!data) {
    throw new Error('Detach payment method response missing.');
  }

  return data;
}

export async function previewTenantUpcomingInvoice(
  tenantId: string,
  payload: UpcomingInvoicePreviewRequest,
  options?: { tenantRole?: string | null },
): Promise<UpcomingInvoicePreviewResponse> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const response = await previewUpcomingInvoiceApiV1BillingTenantsTenantIdUpcomingInvoicePost({
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
    throw new Error('Upcoming invoice preview returned empty payload.');
  }

  return data;
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
