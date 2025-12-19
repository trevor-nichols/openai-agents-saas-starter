'use server';

import type { Client } from '@/lib/api/client/client';

const DEFAULT_SSE_HEADERS = {
  'Content-Type': 'text/event-stream',
  'Cache-Control': 'no-cache',
  Connection: 'keep-alive',
} as const;

function mergeIntoHeaders(target: Headers, input?: HeadersInit): void {
  if (!input) return;
  new Headers(input).forEach((value, key) => {
    target.set(key, value);
  });
}

export interface ProxyBackendSseStreamOptions {
  client: Client;
  auth: () => string;
  url: string;
  signal: AbortSignal;
  requestHeaders?: HeadersInit;
  responseHeaders?: HeadersInit;
}

/**
 * Proxy a backend SSE endpoint into a Next.js Response.
 *
 * We intentionally fetch the backend stream as a raw `ReadableStream` rather than
 * using the generated `.sse.*` helpers because the web app needs to forward the
 * SSE framing unchanged to the browser.
 */
export async function proxyBackendSseStream(options: ProxyBackendSseStreamOptions): Promise<Response> {
  const requestHeaders = new Headers(options.requestHeaders);
  requestHeaders.set('Accept', 'text/event-stream');

  const upstream = await options.client.get({
    url: options.url,
    security: [
      {
        scheme: 'bearer',
        type: 'http',
      },
    ],
    auth: options.auth,
    signal: options.signal,
    cache: 'no-store',
    parseAs: 'stream',
    responseStyle: 'fields',
    throwOnError: true,
    headers: requestHeaders,
  });

  const stream = (upstream as { data?: unknown }).data;
  const upstreamResponse = (upstream as { response?: Response }).response;

  if (!stream || !upstreamResponse) {
    throw new Error('SSE upstream returned no stream.');
  }

  const responseHeaders = new Headers(DEFAULT_SSE_HEADERS);
  mergeIntoHeaders(responseHeaders, options.responseHeaders);

  const contentType = upstreamResponse.headers.get('Content-Type');
  if (contentType) {
    responseHeaders.set('Content-Type', contentType);
  }

  return new Response(stream as BodyInit, {
    status: upstreamResponse.status,
    statusText: upstreamResponse.statusText,
    headers: responseHeaders,
  });
}
