'use server';

import {
  deleteConversationApiV1ConversationsConversationIdDelete,
  getConversationApiV1ConversationsConversationIdGet,
  getConversationEventsApiV1ConversationsConversationIdEventsGet,
  listConversationsApiV1ConversationsGet,
  searchConversationsApiV1ConversationsSearchGet,
} from '@/lib/api/client/sdk.gen';
import type {
  ConversationHistory,
  ConversationEventsResponse,
  ConversationListResponse as BackendConversationListResponse,
  ConversationSearchResponse as BackendConversationSearchResponse,
} from '@/lib/api/client/types.gen';
import type {
  ConversationEvents,
  ConversationListItem,
  ConversationListPage,
  ConversationSearchPage,
} from '@/types/conversations';

import { getServerApiClient } from '../apiClient';

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

function mapSummaryToListItem(summary: {
  conversation_id: string;
  agent_entrypoint?: string | null;
  active_agent?: string | null;
  topic_hint?: string | null;
  status?: string | null;
  message_count?: number;
  last_message_preview?: string | null;
  updated_at: string;
  created_at?: string;
}): ConversationListItem {
  return {
    id: summary.conversation_id,
    agent_entrypoint: summary.agent_entrypoint ?? null,
    active_agent: summary.active_agent ?? null,
    topic_hint: summary.topic_hint ?? null,
    title: summary.topic_hint ?? null,
    status: summary.status ?? null,
    message_count: summary.message_count ?? 0,
    last_message_preview: summary.last_message_preview ?? undefined,
    created_at: summary.created_at,
    updated_at: summary.updated_at,
  };
}
