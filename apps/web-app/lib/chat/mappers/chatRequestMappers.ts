import type { LocationHint } from '@/lib/api/client/types.gen';
import type {
  ConversationHistory,
  ConversationListItem,
  ConversationMessage,
} from '@/types/conversations';
import type { ChatMessage } from '../types';

export function mapHistoryToChatMessages(history: ConversationHistory): ChatMessage[] {
  return history.messages
    .filter((message: ConversationMessage) => message.role !== 'system' || message.content.trim().length > 0)
    .map((message: ConversationMessage, index: number) => {
      const normalizedRole: ChatMessage['role'] = message.role === 'user' ? 'user' : 'assistant';
      const content = message.role === 'system' ? `[system] ${message.content}` : message.content;
      return {
        id: message.timestamp ?? `${normalizedRole}-${history.conversation_id}-${index}`,
        role: normalizedRole,
        content,
        timestamp: message.timestamp ?? undefined,
        attachments: message.attachments ?? null,
      };
    });
}

export function normalizeLocationPayload(
  shareLocation: boolean,
  location?: Partial<LocationHint> | null,
) {
  if (!shareLocation || !location) return undefined;
  return {
    city: location.city?.trim() || undefined,
    region: location.region?.trim() || undefined,
    country: location.country?.trim() || undefined,
    timezone: location.timezone?.trim() || undefined,
  };
}

export function createConversationListEntry(
  messageText: string,
  conversationId: string,
): ConversationListItem {
  const summary = messageText.substring(0, 50) + (messageText.length > 50 ? '...' : '');
  return {
    id: conversationId,
    last_message_preview: summary,
    updated_at: new Date().toISOString(),
  };
}
