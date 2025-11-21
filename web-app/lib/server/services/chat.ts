'use server';

import {
  chatWithAgentApiV1ChatPost,
  streamChatWithAgentApiV1ChatStreamPost,
} from '@/lib/api/client/sdk.gen';
import type {
  AgentChatRequest,
  AgentChatResponse,
} from '@/lib/api/client/types.gen';
import { USE_API_MOCK } from '@/lib/config';

import { getServerApiClient } from '../apiClient';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

export interface ChatStreamOptions {
  signal: AbortSignal;
}

/**
 * Invoke the streaming chat endpoint and return a Response that can be piped
 * directly to the client.
 */
export async function openChatStream(
  payload: AgentChatRequest,
  options: ChatStreamOptions,
): Promise<Response> {
  if (USE_API_MOCK) {
    return createMockChatStream();
  }

  const { client, auth } = await getServerApiClient();
  const upstream = await streamChatWithAgentApiV1ChatStreamPost({
    client,
    auth,
    body: payload,
    signal: options.signal,
    cache: 'no-store',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
    },
    parseAs: 'stream',
    responseStyle: 'fields',
    throwOnError: true,
  });

  const stream = upstream.data;
  if (!stream || !upstream.response) {
    throw new Error('Chat stream returned no data.');
  }

  const headers = new Headers(STREAM_HEADERS);
  const contentType = upstream.response.headers.get('Content-Type');
  if (contentType) {
    headers.set('Content-Type', contentType);
  }

  return new Response(stream as BodyInit, {
    status: upstream.response.status,
    statusText: upstream.response.statusText,
    headers,
  });
}

/**
 * Convenience helper for the non-streaming chat endpoint.
 */
export async function sendChatMessage(payload: AgentChatRequest): Promise<AgentChatResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await chatWithAgentApiV1ChatPost({
    client,
    auth,
    body: payload,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.data) {
    throw new Error('Chat response payload missing.');
  }

  return response.data;
}

function createMockChatStream(): Response {
  const encoder = new TextEncoder();
  const stream = new ReadableStream<Uint8Array>({
    start(controller) {
      const chunk = {
        chunk: 'Hello from mock agent! ',
        conversation_id: 'mock-conversation',
        is_complete: false,
      };
      controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));
      controller.enqueue(
        encoder.encode(
          `data: ${JSON.stringify({ ...chunk, chunk: 'Done.', is_complete: true })}\n\n`,
        ),
      );
      controller.close();
    },
  });

  return new Response(stream, {
    status: 200,
    headers: STREAM_HEADERS,
  });
}
