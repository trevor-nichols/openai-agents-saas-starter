import type {
  ChatMessage as BackendChatMessage,
  ConversationHistory as BackendConversationHistory,
} from '@/lib/api/client/types.gen';

export interface ConversationListItem {
  id: string;
  title?: string;
  last_message_summary?: string;
  updated_at: string;
}

export interface ConversationListResponse {
  success: boolean;
  conversations?: ConversationListItem[];
  error?: string;
}

export type ConversationHistory = BackendConversationHistory;

export type ConversationMessage = BackendChatMessage;
