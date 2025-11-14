'use server';

import {
  deleteConversationApiV1ConversationsConversationIdDelete,
  getConversationApiV1ConversationsConversationIdGet,
  listConversationsApiV1ConversationsGet,
} from '@/lib/api/client/sdk.gen';
import type { ConversationHistory, ConversationSummary } from '@/lib/api/client/types.gen';
import type { ConversationListItem } from '@/types/conversations';

import { getServerApiClient } from '../apiClient';

/**
 * Fetch the authenticated user's conversation summaries from the backend.
 * Converts the backend payload into the UI-facing ConversationListItem shape.
 */
export async function listConversations(): Promise<ConversationListItem[]> {
  const { client, auth } = await getServerApiClient();

  const response = await listConversationsApiV1ConversationsGet({
    client,
    auth,
    responseStyle: 'data',
    throwOnError: true,
  });

  const summaries = response.data ?? [];

  return summaries.map(mapSummaryToListItem);
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

function mapSummaryToListItem(summary: ConversationSummary): ConversationListItem {
  const lastMessage = summary.last_message?.trim();

  return {
    id: summary.conversation_id,
    title: lastMessage || undefined,
    last_message_summary: lastMessage || undefined,
    updated_at: summary.updated_at,
  };
}
