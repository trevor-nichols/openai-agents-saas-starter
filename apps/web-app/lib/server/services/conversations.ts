'use server';

import {
  deleteConversationApiV1ConversationsConversationIdDelete,
  getConversationApiV1ConversationsConversationIdGet,
  getConversationEventsApiV1ConversationsConversationIdEventsGet,
  getConversationMessagesApiV1ConversationsConversationIdMessagesGet,
  listConversationsApiV1ConversationsGet,
  searchConversationsApiV1ConversationsSearchGet,
  streamConversationMetadataApiV1ConversationsConversationIdStreamGet,
  updateConversationMemoryApiV1ConversationsConversationIdMemoryPatch,
  updateConversationTitleApiV1ConversationsConversationIdTitlePatch,
} from '@/lib/api/client/sdk.gen';
import type {
  ConversationHistory,
  ConversationEventsResponse,
  ConversationListResponse as BackendConversationListResponse,
  ConversationSearchResponse as BackendConversationSearchResponse,
  PaginatedMessagesResponse,
  ConversationMemoryConfigRequest,
  ConversationMemoryConfigResponse,
  ConversationTitleUpdateRequest,
  ConversationTitleUpdateResponse,
} from '@/lib/api/client/types.gen';
import type {
  ConversationEvents,
  ConversationListItem,
  ConversationListPage,
  ConversationSearchPage,
  ConversationMessagesPage,
} from '@/types/conversations';

import { getServerApiClient } from '../apiClient';
import { ConversationTitleApiError } from './conversations.errors';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

type SdkFieldsResult<T> =
  | {
      data: T;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

function mapApiErrorMessage(payload: unknown, fallback: string): string {
  if (typeof payload === 'string') {
    return payload || fallback;
  }

  if (!payload || typeof payload !== 'object') {
    return fallback;
  }

  const record = payload as Record<string, unknown>;
  if (typeof record.detail === 'string' && record.detail) return record.detail;
  if (typeof record.message === 'string' && record.message) return record.message;

  const detail = record.detail;
  if (Array.isArray(detail) && detail.length > 0) {
    const parts = detail
      .map((item) => {
        if (item && typeof item === 'object' && typeof (item as Record<string, unknown>).msg === 'string') {
          return (item as Record<string, unknown>).msg as string;
        }
        if (typeof item === 'string') return item;
        return null;
      })
      .filter(Boolean);
    if (parts.length > 0) {
      return parts.join('; ');
    }
  }

  return fallback;
}

/**
 * Fetch the authenticated user's conversation summaries (paginated).
 */
export async function listConversationsPage(params?: {
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}): Promise<ConversationListPage> {
  const { client, auth } = await getServerApiClient();

  const response = await listConversationsApiV1ConversationsGet({
    client,
    auth,
    responseStyle: 'data',
    throwOnError: true,
    query: {
      limit: params?.limit,
      cursor: params?.cursor ?? undefined,
      agent: params?.agent ?? undefined,
    },
  });

  // The generated client returns plain data when responseStyle==='data'. Be defensive
  // because upstream errors or empty bodies can come back as undefined/null.
  const payload = response as unknown as
    | BackendConversationListResponse
    | BackendConversationListResponse['items']
    | undefined
    | null
    | string;

  if (!payload) {
    return { items: [], next_cursor: null };
  }

  if (Array.isArray(payload)) {
    const items = payload.map(mapSummaryToListItem);
    return { items, next_cursor: null };
  }

  const safeItems = Array.isArray((payload as BackendConversationListResponse).items)
    ? (payload as BackendConversationListResponse).items
    : [];

  return {
    items: safeItems.map(mapSummaryToListItem),
    next_cursor: (payload as BackendConversationListResponse).next_cursor ?? null,
  };
}

/**
 * Search conversations by text. Uses direct fetch to the backend search endpoint to
 * avoid SDK staleness while OpenAPI spec catches up.
 */
export async function searchConversationsPage(params: {
  query: string;
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}): Promise<ConversationSearchPage> {
  const { client, auth } = await getServerApiClient();

  const response = await searchConversationsApiV1ConversationsSearchGet({
    client,
    auth,
    responseStyle: 'data',
    throwOnError: true,
    query: {
      q: params.query,
      limit: params.limit,
      cursor: params.cursor ?? undefined,
      agent: params.agent ?? undefined,
    },
  });

  const data = response.data as BackendConversationSearchResponse;

  return {
    items:
      data.items?.map((item) => ({
        conversation_id: item.conversation_id,
        display_name: item.display_name ?? null,
        display_name_pending: false,
        agent_entrypoint: item.agent_entrypoint ?? null,
        active_agent: item.active_agent ?? null,
        topic_hint: item.topic_hint ?? null,
        status: item.status ?? null,
        preview: item.preview,
        last_message_preview: item.last_message_preview ?? item.preview,
        score: item.score ?? undefined,
        updated_at: item.updated_at ?? undefined,
      })) ?? [],
    next_cursor: data.next_cursor ?? null,
  };
}

/**
 * Retrieve a full conversation history for the given identifier.
 */
export async function getConversationHistory(
  conversationId: string,
): Promise<ConversationHistory> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();

  const response = await getConversationApiV1ConversationsConversationIdGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      conversation_id: conversationId,
    },
  });

  const history = response.data;
  if (!history) {
    throw new Error('Conversation not found.');
  }

  return history;
}

export async function getConversationEvents(
  conversationId: string,
  options?: { workflowRunId?: string | null },
): Promise<ConversationEvents> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();

  const response = await getConversationEventsApiV1ConversationsConversationIdEventsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      conversation_id: conversationId,
    },
    query: {
      workflow_run_id: options?.workflowRunId ?? undefined,
    },
  });

  const events = response.data as ConversationEventsResponse | null;
  if (!events) {
    throw new Error('Conversation events not found.');
  }

  return events;
}

/**
 * Retrieve a paginated slice of messages for a conversation.
 */
export async function getConversationMessagesPage(
  conversationId: string,
  options?: { cursor?: string | null; limit?: number; direction?: 'asc' | 'desc' },
): Promise<ConversationMessagesPage> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();

  const response = await getConversationMessagesApiV1ConversationsConversationIdMessagesGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      conversation_id: conversationId,
    },
    query: {
      cursor: options?.cursor ?? undefined,
      limit: options?.limit,
      direction: options?.direction,
    },
  });

  const payload = response.data as PaginatedMessagesResponse | null;

  if (!payload) {
    return { items: [], next_cursor: null, prev_cursor: null };
  }

  return {
    items: payload.items ?? [],
    next_cursor: payload.next_cursor ?? null,
    prev_cursor: payload.prev_cursor ?? null,
  };
}

/**
 * Remove a stored conversation history.
 */
export async function deleteConversation(conversationId: string): Promise<void> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();

  await deleteConversationApiV1ConversationsConversationIdDelete({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      conversation_id: conversationId,
    },
  });
}

/**
 * Update conversation-level memory configuration.
 */
export async function updateConversationMemory(
  conversationId: string,
  config: ConversationMemoryConfigRequest,
  options?: { tenantId?: string | null; tenantRole?: string | null },
): Promise<ConversationMemoryConfigResponse> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const headers = new Headers();
  if (options?.tenantId) {
    headers.set('X-Tenant-Id', options.tenantId);
  }
  if (options?.tenantRole) {
    headers.set('X-Tenant-Role', options.tenantRole);
  }

  const result = await updateConversationMemoryApiV1ConversationsConversationIdMemoryPatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    headers: headers.keys().next().done ? undefined : headers,
    path: { conversation_id: conversationId },
    body: config,
  });

  const payload = result.data as ConversationMemoryConfigResponse | null | undefined;
  if (!payload) {
    throw new Error('Failed to update conversation memory configuration.');
  }
  return payload;
}

/**
 * Update conversation title (manual rename).
 */
export async function updateConversationTitle(
  conversationId: string,
  payload: ConversationTitleUpdateRequest,
  options?: { tenantId?: string | null; tenantRole?: string | null },
): Promise<ConversationTitleUpdateResponse> {
  if (!conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();
  const headers = new Headers();
  if (options?.tenantId) {
    headers.set('X-Tenant-Id', options.tenantId);
  }
  if (options?.tenantRole) {
    headers.set('X-Tenant-Role', options.tenantRole);
  }

  const result = (await updateConversationTitleApiV1ConversationsConversationIdTitlePatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: headers.keys().next().done ? undefined : headers,
    path: { conversation_id: conversationId },
    body: payload,
  })) as SdkFieldsResult<ConversationTitleUpdateResponse>;

  if (result.error) {
    throw new ConversationTitleApiError(
      result.response.status,
      mapApiErrorMessage(result.error, 'Failed to update conversation title.'),
    );
  }

  if (!result.data) {
    throw new ConversationTitleApiError(result.response.status || 500, 'Failed to update conversation title.');
  }

  return result.data;
}

export interface ConversationTitleStreamOptions {
  conversationId: string;
  signal: AbortSignal;
  tenantRole?: string | null;
}

/**
  * Open the SSE stream for the conversation title (generated server-side).
  */
export async function openConversationTitleStream(
  options: ConversationTitleStreamOptions,
): Promise<Response> {
  if (!options.conversationId) {
    throw new Error('Conversation id is required.');
  }

  const { client, auth } = await getServerApiClient();

  const headers = new Headers({
    Accept: 'text/event-stream',
    ...(options.tenantRole ? { 'X-Tenant-Role': options.tenantRole } : {}),
  });

  const upstream = await streamConversationMetadataApiV1ConversationsConversationIdStreamGet({
    client,
    auth,
    signal: options.signal,
    cache: 'no-store',
    headers,
    path: { conversation_id: options.conversationId },
    parseAs: 'stream',
    responseStyle: 'fields',
    throwOnError: true,
  });

  const stream = upstream.data;
  if (!stream || !upstream.response) {
    throw new Error('Conversation title stream returned no data.');
  }

  const responseHeaders = new Headers(STREAM_HEADERS);
  const contentType = upstream.response.headers.get('Content-Type');
  if (contentType) {
    responseHeaders.set('Content-Type', contentType);
  }

  // Upstream is typed loosely by the generated SDK; treat it as a standard SSE body.
  return new Response(stream as unknown as BodyInit, {
    status: upstream.response.status,
    statusText: upstream.response.statusText,
    headers: responseHeaders,
  });
}

function mapSummaryToListItem(summary: {
  conversation_id: string;
  display_name?: string | null;
  display_name_pending?: boolean;
  agent_entrypoint?: string | null;
  active_agent?: string | null;
  topic_hint?: string | null;
  status?: string | null;
  message_count?: number;
  last_message_preview?: string | null;
  updated_at: string;
  created_at?: string;
}): ConversationListItem {
  const title = summary.display_name ?? summary.topic_hint ?? summary.last_message_preview ?? null;
  return {
    id: summary.conversation_id,
    display_name: summary.display_name ?? null,
    display_name_pending: summary.display_name_pending ?? false,
    agent_entrypoint: summary.agent_entrypoint ?? null,
    active_agent: summary.active_agent ?? null,
    topic_hint: summary.topic_hint ?? null,
    title,
    status: summary.status ?? null,
    message_count: summary.message_count ?? 0,
    last_message_preview: summary.last_message_preview ?? undefined,
    created_at: summary.created_at,
    updated_at: summary.updated_at,
  };
}
