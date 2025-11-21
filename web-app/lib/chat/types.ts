export interface StreamChatParams {
  message: string;
  conversationId?: string | null;
  agentType?: string | null;
}

export interface StreamChunk {
  type: 'content' | 'error';
  payload: string;
  conversationId?: string;
}

export interface BackendStreamData {
  chunk: string;
  conversation_id: string;
  is_complete: boolean;
  error?: string;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  isStreaming?: boolean;
}
