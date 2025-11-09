'use server';

import { authenticatedFetch } from '@/lib/auth/http';
import { streamChat, type StreamChunk } from '@/lib/api/streaming';
import type { ConversationListItem } from '@/types/conversations';

// Server Action for streaming chat with agents
export async function* streamChatAgent(params: {
  message: string;
  conversationId?: string | null;
  agentType?: string | null;
}): AsyncGenerator<StreamChunk, void, undefined> {
  try {
    const stream = streamChat({
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

// Server Action for listing conversations
export async function listConversationsAction() {
  try {
    const response = await authenticatedFetch('/api/v1/conversations', {
      method: 'GET',
    });
    const payload = await response.json();
    const conversations = (payload?.data ?? []) as ConversationListItem[];
    return {
      success: true,
      conversations,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch conversations',
    };
  }
}
