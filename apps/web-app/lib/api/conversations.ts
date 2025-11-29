/**
 * API Layer - Pure functions for conversations API
 *
 * Separation of concerns:
 * - No React dependencies
 * - Fully typed
 * - Testable without React
 * - Reusable across different contexts
 */

import type {
  ConversationHistory,
  ConversationListItem,
  ConversationListPage,
  ConversationSearchPage,
} from '@/types/conversations';

/**
 * Fetch paginated conversations for the current user
 */
export async function fetchConversationsPage(params?: {
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}): Promise<ConversationListPage> {
  const searchParams = new URLSearchParams();
  if (params?.limit) searchParams.set('limit', String(params.limit));
  if (params?.cursor) searchParams.set('cursor', params.cursor);
  if (params?.agent) searchParams.set('agent', params.agent);

  const response = await fetch(`/api/conversations${searchParams.toString() ? `?${searchParams.toString()}` : ''}`);
  if (!response.ok) {
    throw new Error('Failed to load conversations');
  }

  const result = (await response.json()) as ConversationListPage;
  return {
    items: result.items ?? [],
    next_cursor: result.next_cursor ?? null,
  };
}

/**
 * Helper to sort conversations by updated_at (newest first)
 */
export function sortConversationsByDate(
  conversations: ConversationListItem[]
): ConversationListItem[] {
  return [...conversations].sort(
    (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
  );
}

export async function searchConversations(params: {
  query: string;
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}): Promise<ConversationSearchPage> {
  const searchParams = new URLSearchParams();
  searchParams.set('q', params.query);
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.cursor) searchParams.set('cursor', params.cursor);
  if (params.agent) searchParams.set('agent', params.agent);

  const response = await fetch(`/api/conversations/search?${searchParams.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to search conversations');
  }

  const result = (await response.json()) as ConversationSearchPage;
  return {
    items: result.items ?? [],
    next_cursor: result.next_cursor ?? null,
  };
}

/**
 * Fetch the detailed history for a specific conversation.
 */
export async function fetchConversationHistory(
  conversationId: string,
): Promise<ConversationHistory> {
  const response = await fetch(`/api/conversations/${conversationId}`, {
    method: 'GET',
    cache: 'no-store',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load conversation history');
  }

  return (await response.json()) as ConversationHistory;
}

/**
 * Delete a stored conversation by id.
 */
export async function deleteConversationById(conversationId: string): Promise<void> {
  const response = await fetch(`/api/conversations/${conversationId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to delete conversation');
  }
}
