/**
 * SSE client for conversation metadata events (e.g., generated titles).
 *
 * Browser-only; auth is handled by the BFF route via cookies.
 */

export type ConversationMetadataHandler = (event: { data: unknown }) => void;

export interface ConversationMetadataStreamOptions {
  conversationId: string;
  onEvent: ConversationMetadataHandler;
  onError?: (error: Event) => void;
  onOpen?: () => void;
}

export function openConversationMetadataStream(options: ConversationMetadataStreamOptions): EventSource {
  const { conversationId } = options;
  const url = `/api/v1/conversations/${encodeURIComponent(conversationId)}/stream`;

  const source = new EventSource(url);

  source.onmessage = (event) => {
    if (!event.data) return;
    try {
      const parsed = JSON.parse(event.data);
      options.onEvent({ data: parsed });
    } catch {
      options.onEvent({ data: event.data });
    }
  };

  if (options.onError) {
    source.onerror = options.onError;
  }
  if (options.onOpen) {
    source.onopen = options.onOpen;
  }

  return source;
}

