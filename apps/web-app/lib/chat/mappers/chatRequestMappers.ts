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

export function mapMessagesToChatMessages(
  messages: ConversationMessage[],
  conversationId?: string,
): ChatMessage[] {
  return messages
    .filter((message) => message.role !== 'system' || message.content.trim().length > 0)
    .map((message, index) => {
      const normalizedRole: ChatMessage['role'] = message.role === 'user' ? 'user' : 'assistant';
      const content = message.role === 'system' ? `[system] ${message.content}` : message.content;
      return {
        id: message.timestamp ?? `${normalizedRole}-${conversationId ?? 'conversation'}-${index}`,
        role: normalizedRole,
        content,
        timestamp: message.timestamp ?? undefined,
        attachments: message.attachments ?? null,
      };
    });
}

export function dedupeAndSortMessages(messages: ChatMessage[]): ChatMessage[] {
  const byKey = new Map<
    string,
    { message: ChatMessage; isPlaceholder: boolean }
  >();

  messages.forEach((message, index) => {
    const isPlaceholder =
      typeof message.id === 'string' && /^(user|assistant)-\d+/.test(message.id);
    const bucket =
      message.timestamp !== undefined && message.timestamp !== null
        ? Math.floor(Date.parse(message.timestamp) / 1000)
        : 'no-ts';
    const contentKey = `${bucket}-${message.role}-${message.content}`;

    const existing = byKey.get(contentKey);
    if (!existing) {
      byKey.set(contentKey, { message, isPlaceholder });
      return;
    }

    if (existing.isPlaceholder && !isPlaceholder) {
      // Replace optimistic placeholder with persisted copy
      byKey.set(contentKey, { message, isPlaceholder });
      return;
    }

    if (!existing.isPlaceholder && isPlaceholder) {
      // Keep existing real message; drop placeholder
      return;
    }

    // Same kind (both real or both placeholder) with identical bucket/content:
    // preserve distinct turns by giving them unique composite keys.
    const altKey = `${contentKey}::${index}`;
    byKey.set(altKey, { message, isPlaceholder });
  });

  return Array.from(byKey.values())
    .map((entry) => entry.message)
    .sort((a, b) => {
      const aTime = a.timestamp ? Date.parse(a.timestamp) : 0;
      const bTime = b.timestamp ? Date.parse(b.timestamp) : 0;
      return aTime - bTime;
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
