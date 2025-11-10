'use server';

import type { StreamChunk } from '@/lib/chat/types';
import { streamChatServer } from '@/lib/server/streaming/chat';
import { listConversations } from '@/lib/server/services/conversations';

// Server Action for streaming chat with agents
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

// Server Action for listing conversations
export async function listConversationsAction() {
  try {
    const conversations = await listConversations();
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
