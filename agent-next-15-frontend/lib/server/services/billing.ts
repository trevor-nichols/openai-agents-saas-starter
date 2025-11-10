'use server';

import {
  billingEventStreamApiV1BillingStreamGet,
  listBillingPlansApiV1BillingPlansGet,
} from '@/lib/api/client/sdk.gen';
import type { BillingPlanResponse } from '@/lib/api/client/types.gen';

import { USE_API_MOCK } from '@/lib/config';

import { getServerApiClient } from '../apiClient';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

export interface BillingStreamOptions {
  signal: AbortSignal;
  tenantRole?: string | null;
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
