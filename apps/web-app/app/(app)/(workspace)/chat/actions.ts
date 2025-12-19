// File Path: app/(app)/(workspace)/chat/actions.ts
// Description: Server Actions powering chat streaming and conversation listing.
// Sections:
// - Stream chat: Proxy streaming responses from the backend.
// - List conversations: Fetch conversation summaries for the workspace.

'use server';

import { streamChat } from '@/lib/api/chat';
import { fetchConversationsPage, searchConversations } from '@/lib/api/conversations';
import type { StreamChunk } from '@/lib/chat/types';

// --- Stream chat ---
// Exposes the streaming chat server action to the client workspace components.
export async function* streamChatAgent(params: {
  message: string;
  conversationId?: string | null;
  agentType?: string | null;
  shareLocation?: boolean;
  location?: {
    city?: string | null;
    region?: string | null;
    country?: string | null;
    timezone?: string | null;
  } | null;
}): AsyncGenerator<StreamChunk, void, undefined> {
  try {
    const stream = streamChat({
      message: params.message,
      conversationId: params.conversationId,
      agentType: params.agentType ?? 'triage',
      shareLocation: params.shareLocation,
      location: params.location,
    });

    for await (const chunk of stream) {
      yield chunk;
    }
  } catch (error) {
    yield {
      type: 'error',
      payload: error instanceof Error ? error.message : 'Streaming failed',
    };
  }
}

// --- List conversations ---
// Enables TanStack Query hooks to fetch the user’s conversations via a server action.
export async function listConversationsAction(params?: {
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}) {
  try {
    const page = await fetchConversationsPage(params);
    return {
      success: true,
      items: page.items,
      next_cursor: page.next_cursor,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch conversations',
    };
  }
}

export async function searchConversationsAction(params: {
  query: string;
  limit?: number;
  cursor?: string | null;
  agent?: string | null;
}) {
  try {
    const page = await searchConversations(params);
    return {
      success: true,
      items: page.items,
      next_cursor: page.next_cursor,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to search conversations',
    };
  }
}
