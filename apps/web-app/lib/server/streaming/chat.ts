import 'server-only';

import { streamChat } from '@/lib/api/chat';
import type { StreamChatParams, StreamChunk } from '@/lib/chat/types';

/**
 * Server-side helper to stream chat chunks through the Next.js proxy routes.
 * Keeps browser callers from reaching the API service directly.
 */
export async function* streamChatServer(
  params: StreamChatParams,
): AsyncGenerator<StreamChunk, void, unknown> {
  for await (const chunk of streamChat(params)) {
    yield chunk;
  }
}
