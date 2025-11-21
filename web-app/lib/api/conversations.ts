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
  ConversationListResponse,
} from '@/types/conversations';

/**
 * Fetch all conversations for the current user
 */
export async function fetchConversations(): Promise<ConversationListItem[]> {
  const response = await fetch('/api/conversations', {
    method: 'GET',
    cache: 'no-store',
  });

  const result = (await response.json()) as ConversationListResponse;

  if (!response.ok) {
    throw new Error(result.error || 'Failed to load conversations');
  }

  if (!result.success || !result.conversations) {
    throw new Error(result.error || 'Unknown error loading conversations');
  }

  return result.conversations;
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
