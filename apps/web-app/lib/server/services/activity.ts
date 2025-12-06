'use server';

import { streamActivityEventsApiV1ActivityStreamGet } from '@/lib/api/client/sdk.gen';
import { USE_API_MOCK } from '@/lib/config';
import { getServerApiClient } from '../apiClient';

const STREAM_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

function assertActivitySdkPresent() {
  if (!streamActivityEventsApiV1ActivityStreamGet) {
    throw new Error(
      'Activity SDK export missing. Regenerate via "pnpm generate:fixtures" with latest OpenAPI.',
    );
  }
}

assertActivitySdkPresent();

export interface ActivityStreamOptions {
  signal: AbortSignal;
}

export async function openActivityStream(options: ActivityStreamOptions): Promise<Response> {
  if (USE_API_MOCK) {
    return new Response('data: {}\n\n', { headers: STREAM_HEADERS });
  }

  const { client, auth } = await getServerApiClient();

  const upstream = await streamActivityEventsApiV1ActivityStreamGet({
    client,
    auth,
    signal: options.signal,
    cache: 'no-store',
    headers: {
      Accept: 'text/event-stream',
    },
    parseAs: 'stream',
    responseStyle: 'fields',
    throwOnError: true,
  });

  const stream = upstream.data;

  if (!stream || !upstream.response) {
    throw new Error('Activity stream returned no data.');
  }

  const responseHeaders = new Headers(STREAM_HEADERS);
  const contentType = upstream.response.headers.get('Content-Type');
  if (contentType) {
    responseHeaders.set('Content-Type', contentType);
  }

  return new Response(stream as BodyInit, {
    status: upstream.response.status,
    statusText: upstream.response.statusText,
    headers: responseHeaders,
  });
}
