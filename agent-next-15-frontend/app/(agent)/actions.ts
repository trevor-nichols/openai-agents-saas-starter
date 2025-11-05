'use server';

import { listConversationsApiV1AgentsConversationsGet } from '@/lib/api/client';
import { streamChat, type StreamChunk } from '@/lib/api/streaming';

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
export interface ConversationListItem {
  id: string;
  title?: string;
  last_message_summary?: string;
  updated_at: string;
}

export async function listConversationsAction() {
  try {
    const { data, error } =
      await listConversationsApiV1AgentsConversationsGet();

    if (error) throw error;

    return {
      success: true,
      conversations: (data as { data?: ConversationListItem[] })?.data ?? [],
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to fetch conversations',
    };
  }
}
