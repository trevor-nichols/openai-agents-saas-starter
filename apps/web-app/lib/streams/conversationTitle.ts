/**
 * SSE client for conversation title generation.
 *
 * Browser-only; auth is handled by the BFF route via cookies.
 */

export type ConversationTitleStreamMessageHandler = (message: string) => void;

export interface ConversationTitleStreamOptions {
  conversationId: string;
  onMessage: ConversationTitleStreamMessageHandler;
  onError?: (error: Event) => void;
  onOpen?: () => void;
}

export function openConversationTitleStream(options: ConversationTitleStreamOptions): EventSource {
  const { conversationId } = options;
  const url = `/api/v1/conversations/${encodeURIComponent(conversationId)}/stream`;

  const source = new EventSource(url);

  source.onmessage = (event) => {
    if (typeof event.data !== 'string' || event.data.length === 0) return;
    options.onMessage(event.data);
  };

  if (options.onError) {
    source.onerror = options.onError;
  }
  if (options.onOpen) {
    source.onopen = options.onOpen;
  }

  return source;
}
