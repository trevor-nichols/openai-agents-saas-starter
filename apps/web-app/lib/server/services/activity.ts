'use server';

import { USE_API_MOCK } from '@/lib/config';
import { getServerApiClient } from '../apiClient';
import { proxyBackendSseStream } from '../streaming/sseProxy';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

export interface ActivityStreamOptions {
  signal: AbortSignal;
}

export async function openActivityStream(options: ActivityStreamOptions): Promise<Response> {
  if (USE_API_MOCK) {
    return new Response('data: {}\n\n', { headers: STREAM_HEADERS });
  }

  const { client, auth } = await getServerApiClient();

  return proxyBackendSseStream({
    client,
    auth,
    url: '/api/v1/activity/stream',
    signal: options.signal,
  });
}
