'use server';

import {
  deleteConversationApiV1ConversationsConversationIdDelete,
  getConversationApiV1ConversationsConversationIdGet,
  listConversationsApiV1ConversationsGet,
  searchConversationsApiV1ConversationsSearchGet,
} from '@/lib/api/client/sdk.gen';
import type {
  ConversationHistory,
  ConversationListResponse as BackendConversationListResponse,
  ConversationSearchResponse as BackendConversationSearchResponse,
} from '@/lib/api/client/types.gen';
import type {
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

  const payload = response.data as BackendConversationListResponse | BackendConversationListResponse['items'];

  if (Array.isArray(payload)) {
    const items = payload.map(mapSummaryToListItem);
    return { items, next_cursor: null };
  }

  const items = (payload.items ?? []).map(mapSummaryToListItem);
  return { items, next_cursor: payload.next_cursor ?? null };
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
        preview: item.preview,
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

function mapSummaryToListItem(summary: { conversation_id: string; last_message?: string | null; updated_at: string; created_at?: string; message_count?: number }): ConversationListItem {
  const lastMessage = summary.last_message?.trim();

  return {
    id: summary.conversation_id,
    title: lastMessage || undefined,
    last_message_summary: lastMessage || undefined,
    updated_at: summary.updated_at,
  };
}
