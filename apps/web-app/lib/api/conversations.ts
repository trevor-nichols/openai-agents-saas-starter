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
  ConversationEvents,
  ConversationMessagesPage,
} from '@/types/conversations';
import { apiV1Path } from '@/lib/apiPaths';

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

  const response = await fetch(
    `${apiV1Path('/conversations')}${searchParams.toString() ? `?${searchParams.toString()}` : ''}`,
  );
  if (!response.ok) {
    throw new Error('Failed to load conversations');
  }

  const result = (await response.json()) as ConversationListPage;
  return {
    items:
      result.items?.map((item) => ({
        ...item,
        display_name: item.display_name ?? null,
        display_name_pending: item.display_name_pending ?? false,
        title: item.display_name ?? item.topic_hint ?? item.last_message_preview ?? null,
      })) ?? [],
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

  const response = await fetch(`${apiV1Path('/conversations/search')}?${searchParams.toString()}`);
  if (!response.ok) {
    throw new Error('Failed to search conversations');
  }

  const result = (await response.json()) as {
    items?: Array<{
      conversation_id: string;
      display_name?: string | null;
      display_name_pending?: boolean;
      agent_entrypoint?: string | null;
      active_agent?: string | null;
      topic_hint?: string | null;
      status?: string | null;
      preview: string;
      last_message_preview?: string | null;
      score?: number | null;
      updated_at?: string | null;
    }>;
    next_cursor?: string | null;
  };

  return {
    items: (result.items ?? []).map((item) => ({
      conversation_id: item.conversation_id,
      display_name: item.display_name ?? null,
      display_name_pending: item.display_name_pending ?? false,
      agent_entrypoint: item.agent_entrypoint ?? null,
      active_agent: item.active_agent ?? null,
      topic_hint: item.topic_hint ?? null,
      status: item.status ?? null,
      preview: item.preview,
      last_message_preview: item.last_message_preview ?? item.preview,
      score: item.score,
      updated_at: item.updated_at ?? null,
    })),
    next_cursor: result.next_cursor ?? null,
  };
}

/**
 * Fetch the detailed history for a specific conversation.
 */
export async function fetchConversationHistory(
  conversationId: string,
): Promise<ConversationHistory> {
  const response = await fetch(apiV1Path(`/conversations/${encodeURIComponent(conversationId)}`), {
    method: 'GET',
    cache: 'no-store',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load conversation history');
  }

  return (await response.json()) as ConversationHistory;
}

export async function fetchConversationMessages(params: {
  conversationId: string;
  limit?: number;
  cursor?: string | null;
  direction?: 'asc' | 'desc';
}): Promise<ConversationMessagesPage> {
  const searchParams = new URLSearchParams();
  if (params.limit) searchParams.set('limit', String(params.limit));
  if (params.cursor) searchParams.set('cursor', params.cursor);
  if (params.direction) searchParams.set('direction', params.direction);

  const response = await fetch(
    `${apiV1Path(`/conversations/${encodeURIComponent(params.conversationId)}/messages`)}${
      searchParams.toString() ? `?${searchParams.toString()}` : ''
    }`,
    {
      method: 'GET',
      cache: 'no-store',
    },
  );

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to load conversation messages');
  }

  const page = (await response.json()) as ConversationMessagesPage;
  return {
    items: page.items ?? [],
    next_cursor: page.next_cursor ?? null,
    prev_cursor: page.prev_cursor ?? null,
  };
}

export async function fetchConversationEvents(params: {
  conversationId: string;
  workflowRunId?: string | null;
}): Promise<ConversationEvents> {
  const { conversationId, workflowRunId } = params;

  const searchParams = new URLSearchParams();
  if (workflowRunId) searchParams.set('workflow_run_id', workflowRunId);

  const response = await fetch(
    `${apiV1Path(`/conversations/${encodeURIComponent(conversationId)}/events`)}${
      searchParams.toString() ? `?${searchParams.toString()}` : ''
    }`,
    {
      method: 'GET',
      cache: 'no-store',
    },
  );

  if (!response.ok) {
    const payload = (await response.json().catch(() => ({}))) as { error?: string; message?: string };
    throw new Error(payload.error || payload.message || 'Failed to load conversation events');
  }

  const body = (await response.json().catch(() => null)) as
    | { success?: boolean; data?: ConversationEvents; error?: string; message?: string }
    | null;

  if (!body || body.success === false) {
    const errMsg = body?.error || body?.message || 'Failed to load conversation events';
    throw new Error(errMsg);
  }

  if (!body?.data) {
    throw new Error('Conversation events payload was empty');
  }

  return body.data;
}

/**
 * Delete a stored conversation by id.
 */
export async function deleteConversationById(conversationId: string): Promise<void> {
  const response = await fetch(apiV1Path(`/conversations/${encodeURIComponent(conversationId)}`), {
    method: 'DELETE',
  });

  if (!response.ok) {
    const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
    throw new Error(errorPayload.message || 'Failed to delete conversation');
  }
}
