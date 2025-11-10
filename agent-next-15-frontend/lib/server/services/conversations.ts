'use server';

import { listConversationsApiV1ConversationsGet } from '@/lib/api/client/sdk.gen';
import type { ConversationSummary } from '@/lib/api/client/types.gen';
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

function mapSummaryToListItem(summary: ConversationSummary): ConversationListItem {
  const lastMessage = summary.last_message?.trim();

  return {
    id: summary.conversation_id,
    title: lastMessage || undefined,
    last_message_summary: lastMessage || undefined,
    updated_at: summary.updated_at,
  };
}
