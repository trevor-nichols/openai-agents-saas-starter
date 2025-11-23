// File Path: app/(app)/(workspace)/chat/actions.ts
// Description: Server Actions powering chat streaming and conversation listing.
// Sections:
// - Stream chat: Proxy streaming responses from the backend.
// - List conversations: Fetch conversation summaries for the workspace.

'use server';

import type { StreamChunk } from '@/lib/chat/types';
import { streamChatServer } from '@/lib/server/streaming/chat';
import {
  listConversationsPage,
  searchConversationsPage,
} from '@/lib/server/services/conversations';

// --- Stream chat ---
// Exposes the streaming chat server action to the client workspace components.
export async function* streamChatAgent(params: {
  message: string;
  conversationId?: string | null;
  agentType?: string | null;
}): AsyncGenerator<StreamChunk, void, undefined> {
  try {
    const stream = streamChatServer({
      message: params.message,
      conversationId: params.conversationId,
      agentType: params.agentType ?? 'triage',
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
    const page = await listConversationsPage(params);
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
    const page = await searchConversationsPage(params);
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
