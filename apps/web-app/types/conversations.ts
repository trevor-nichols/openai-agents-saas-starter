import type {
  ChatMessage as BackendChatMessage,
  ConversationHistory as BackendConversationHistory,
  ConversationEventItem as BackendConversationEventItem,
  ConversationEventsResponse as BackendConversationEventsResponse,
  ConversationLedgerEventsResponse as BackendConversationLedgerEventsResponse,
  PaginatedMessagesResponse,
  ConversationMemoryConfigRequest,
  ConversationMemoryConfigResponse,
  ConversationTitleUpdateRequest,
  ConversationTitleUpdateResponse,
} from '@/lib/api/client/types.gen';

export interface ConversationListItem {
  id: string;
  display_name?: string | null;
  display_name_pending?: boolean;
  agent_entrypoint?: string | null;
  active_agent?: string | null;
  title?: string | null;
  topic_hint?: string | null;
  status?: string | null;
  message_count?: number;
  last_message_preview?: string;
  created_at?: string;
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
}

export interface ConversationSearchPage {
  items: ConversationSearchResultItem[];
  next_cursor: string | null;
}

export type ConversationHistory = BackendConversationHistory;

export type ConversationMessage = BackendChatMessage;

export type ConversationMessagesPage = PaginatedMessagesResponse;

export type ConversationEvent = BackendConversationEventItem;

export type ConversationEvents = BackendConversationEventsResponse;

export type ConversationLedgerEventsPage = BackendConversationLedgerEventsResponse;

export type ConversationMemoryConfig = ConversationMemoryConfigResponse;
export type ConversationMemoryConfigInput = ConversationMemoryConfigRequest;

export type ConversationTitleUpdate = ConversationTitleUpdateResponse;
export type ConversationTitleUpdateInput = ConversationTitleUpdateRequest;
