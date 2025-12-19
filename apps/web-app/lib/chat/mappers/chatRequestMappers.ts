import type { LocationHint } from '@/lib/api/client/types.gen';
import { parseTimestampMs } from '@/lib/utils/time';
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
        id:
          message.message_id ??
          message.timestamp ??
          `${normalizedRole}-${history.conversation_id}-${index}`,
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
        id:
          message.message_id ??
          message.timestamp ??
          `${normalizedRole}-${conversationId ?? 'conversation'}-${index}`,
        role: normalizedRole,
        content,
        timestamp: message.timestamp ?? undefined,
        attachments: message.attachments ?? null,
      };
    });
}

export function dedupeAndSortMessages(messages: ChatMessage[]): ChatMessage[] {
  const PLACEHOLDER_ID_RE = /^(user|assistant)-\d+/;
  const CURSOR_TOKEN = '▋';
  const PLACEHOLDER_MATCH_WINDOW_MS = 2 * 60 * 1000;

  const normalizeContent = (content: string) =>
    content.replace(new RegExp(`${CURSOR_TOKEN}\\s*$`), '').trim();

  const mergePlaceholderMetadata = (persisted: ChatMessage, placeholder: ChatMessage): ChatMessage => {
    const hasPersistedAttachments = Array.isArray(persisted.attachments) && persisted.attachments.length > 0;
    const hasPlaceholderAttachments = Array.isArray(placeholder.attachments) && placeholder.attachments.length > 0;

    return {
      ...persisted,
      citations: persisted.citations ?? placeholder.citations ?? null,
      structuredOutput:
        persisted.structuredOutput !== null && persisted.structuredOutput !== undefined
          ? persisted.structuredOutput
          : (placeholder.structuredOutput ?? null),
      attachments: hasPersistedAttachments
        ? persisted.attachments
        : (hasPlaceholderAttachments ? placeholder.attachments : (persisted.attachments ?? placeholder.attachments ?? null)),
    };
  };

  const byId = new Map<string, ChatMessage>();
  const orderedIds: string[] = [];

  const prefer = (existing: ChatMessage, incoming: ChatMessage): ChatMessage => {
    if (existing.isStreaming && !incoming.isStreaming) return incoming;
    if (!existing.isStreaming && incoming.isStreaming) return existing;
    const existingLen = normalizeContent(existing.content).length;
    const incomingLen = normalizeContent(incoming.content).length;
    if (incomingLen > existingLen) return incoming;
    return existing;
  };

  for (const message of messages) {
    const existing = byId.get(message.id);
    if (!existing) {
      byId.set(message.id, message);
      orderedIds.push(message.id);
      continue;
    }
    byId.set(message.id, prefer(existing, message));
  }

  const uniqueMessages = orderedIds
    .map((id) => byId.get(id))
    .filter((msg): msg is ChatMessage => Boolean(msg));

  type Indexed = {
    message: ChatMessage;
    index: number;
    isPlaceholder: boolean;
    signature: string;
    timestampMs: number | null;
  };

  const indexed: Indexed[] = uniqueMessages.map((message, index) => ({
    message,
    index,
    isPlaceholder: typeof message.id === 'string' && PLACEHOLDER_ID_RE.test(message.id),
    signature: `${message.kind ?? 'message'}:${message.role}:${normalizeContent(message.content)}`,
    timestampMs: parseTimestampMs(message.timestamp),
  }));

  const groups = new Map<string, Indexed[]>();
  indexed.forEach((entry) => {
    const group = groups.get(entry.signature);
    if (group) group.push(entry);
    else groups.set(entry.signature, [entry]);
  });

  const dropPlaceholderIndexes = new Set<number>();
  const mergedMessagesByIndex = new Map<number, ChatMessage>();

  for (const group of groups.values()) {
    const placeholders = group
      .filter((entry) => entry.isPlaceholder)
      .sort((a, b) => (a.timestampMs ?? a.index) - (b.timestampMs ?? b.index));
    const persisted = group
      .filter((entry) => !entry.isPlaceholder)
      .sort((a, b) => (a.timestampMs ?? a.index) - (b.timestampMs ?? b.index));

    if (placeholders.length === 0 || persisted.length === 0) continue;

    let p = 0;
    let r = 0;

    while (p < placeholders.length && r < persisted.length) {
      const placeholder = placeholders[p];
      const real = persisted[r];
      if (!placeholder || !real) break;

      if (placeholder.timestampMs === null || real.timestampMs === null) {
        dropPlaceholderIndexes.add(placeholder.index);
        mergedMessagesByIndex.set(
          real.index,
          mergePlaceholderMetadata(real.message, placeholder.message),
        );
        p += 1;
        r += 1;
        continue;
      }

      const diff = Math.abs(placeholder.timestampMs - real.timestampMs);
      if (diff <= PLACEHOLDER_MATCH_WINDOW_MS) {
        dropPlaceholderIndexes.add(placeholder.index);
        mergedMessagesByIndex.set(
          real.index,
          mergePlaceholderMetadata(real.message, placeholder.message),
        );
        p += 1;
        r += 1;
        continue;
      }

      if (placeholder.timestampMs < real.timestampMs) {
        p += 1;
      } else {
        r += 1;
      }
    }
  }

  return indexed
    .filter((entry) => !(entry.isPlaceholder && dropPlaceholderIndexes.has(entry.index)))
    .sort((a, b) => {
      const aTime = a.timestampMs ?? Number.POSITIVE_INFINITY;
      const bTime = b.timestampMs ?? Number.POSITIVE_INFINITY;
      if (aTime !== bTime) return aTime - bTime;
      return a.index - b.index;
    })
    .map((entry) => mergedMessagesByIndex.get(entry.index) ?? entry.message);
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
