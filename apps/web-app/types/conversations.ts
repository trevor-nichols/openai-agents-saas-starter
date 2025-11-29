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
  items?: ConversationListItem[];
  next_cursor?: string | null;
  error?: string;
}

export interface ConversationListPage {
  items: ConversationListItem[];
  next_cursor: string | null;
}

export interface ConversationSearchResultItem {
  conversation_id: string;
  preview: string;
  score?: number | null;
  updated_at?: string | null;
}

export interface ConversationSearchPage {
  items: ConversationSearchResultItem[];
  next_cursor: string | null;
}

export type ConversationHistory = BackendConversationHistory;

export type ConversationMessage = BackendChatMessage;
