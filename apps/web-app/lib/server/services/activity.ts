import 'server-only';

import {
  dismissActivityApiV1ActivityEventIdDismissPost,
  listActivityEventsApiV1ActivityGet,
  markActivityReadApiV1ActivityEventIdReadPost,
  markAllActivityReadApiV1ActivityMarkAllReadPost,
} from '@/lib/api/client/sdk.gen';
import type { ActivityListResponse, ReceiptResponse } from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';
import { getServerApiClient } from '../apiClient';
import { proxyBackendSseStream } from '../streaming/sseProxy';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

export interface ActivityStreamOptions {
  signal: AbortSignal;
}

export interface ActivityListParams {
  limit?: number;
  cursor?: string | null;
  action?: string | null;
  actorId?: string | null;
  objectType?: string | null;
  objectId?: string | null;
  status?: string | null;
  requestId?: string | null;
  createdAfter?: string | null;
  createdBefore?: string | null;
}

export interface ActivityMutationResult {
  ok: boolean;
  status: number;
  payload: unknown;
}

type ApiFieldsResult<TData> =
  | {
      data: TData;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

function toMutationResult(
  result: ApiFieldsResult<ReceiptResponse>,
): ActivityMutationResult {
  const status = result.response?.status ?? 502;
  if ('error' in result && result.error) {
    return {
      ok: false,
      status,
      payload: result.error,
    };
  }

  return {
    ok: status < 400,
    status,
    payload: result.data ?? { unread_count: 0 },
  };
}

export async function listActivityEvents(params: ActivityListParams): Promise<ActivityListResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await listActivityEventsApiV1ActivityGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      limit: params.limit,
      cursor: params.cursor ?? undefined,
      action: params.action ?? undefined,
      actor_id: params.actorId ?? undefined,
      object_type: params.objectType ?? undefined,
      object_id: params.objectId ?? undefined,
      status: params.status ?? undefined,
      request_id: params.requestId ?? undefined,
      created_after: params.createdAfter ?? undefined,
      created_before: params.createdBefore ?? undefined,
    },
  });

  return response.data ?? { items: [], next_cursor: null, unread_count: 0 };
}

export async function markActivityRead(eventId: string): Promise<ActivityMutationResult> {
  if (!eventId) {
    throw new Error('Event id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const result = (await markActivityReadApiV1ActivityEventIdReadPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: { event_id: eventId },
  })) as ApiFieldsResult<ReceiptResponse>;

  return toMutationResult(result);
}

export async function dismissActivity(eventId: string): Promise<ActivityMutationResult> {
  if (!eventId) {
    throw new Error('Event id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const result = (await dismissActivityApiV1ActivityEventIdDismissPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: { event_id: eventId },
  })) as ApiFieldsResult<ReceiptResponse>;

  return toMutationResult(result);
}

export async function markAllActivityRead(): Promise<ActivityMutationResult> {
  const { client, auth } = await getServerApiClient();
  const result = (await markAllActivityReadApiV1ActivityMarkAllReadPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
  })) as ApiFieldsResult<ReceiptResponse>;

  return toMutationResult(result);
}

export async function openActivityStream(options: ActivityStreamOptions): Promise<Response> {
  if (USE_API_MOCK) {
    return new Response('data: {}\n\n', { headers: STREAM_HEADERS });
  }

  const { client, auth } = await getServerApiClient();

  return proxyBackendSseStream({
    client,
    auth,
    url: '/api/v1/activity/stream',
    signal: options.signal,
  });
}
