/**
 * API Layer - Pure functions for conversations API
 *
 * Separation of concerns:
 * - No React dependencies
 * - Fully typed
 * - Testable without React
 * - Reusable across different contexts
 */

import type { ConversationListItem, ConversationListResponse } from '@/types/conversations';

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
