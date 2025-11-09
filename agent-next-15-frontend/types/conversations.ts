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
