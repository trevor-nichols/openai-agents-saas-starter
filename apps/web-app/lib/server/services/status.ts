import 'server-only';

import { cacheLife, cacheTag } from 'next/cache';

import { getPlatformStatusApiV1StatusGet, getPlatformStatusRssApiV1StatusRssGet } from '@/lib/api/client/sdk.gen';
import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';
import { createApiClient } from '@/lib/server/apiClient';

/**
 * Fetch the latest platform status snapshot from the FastAPI backend.
 */
export async function fetchPlatformStatusSnapshot(): Promise<PlatformStatusResponse> {
  'use cache';
  // Keep status reasonably fresh while still benefiting from prerender caching.
  cacheLife({
    stale: 60, // serve cached for 60s before the client asks again
    revalidate: 60, // background refresh every 60s when traffic continues
    expire: 300, // hard expire after 5 minutes of no traffic
  });
  cacheTag('platform-status');

  const client = createApiClient();

  const response = await getPlatformStatusApiV1StatusGet({
    client,
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Status endpoint returned empty response.');
  }

  return payload;
}

export interface StatusRssResponse {
  status: number;
  body: string;
  contentType: string;
}

function resolveRssBody(error: unknown): string {
  if (!error) return '';
  if (typeof error === 'string') return error;
  try {
    return JSON.stringify(error);
  } catch {
    return '';
  }
}

export async function fetchStatusRss(): Promise<StatusRssResponse> {
  const client = createApiClient();
  const response = await getPlatformStatusRssApiV1StatusRssGet({
    client,
    responseStyle: 'fields',
    throwOnError: false,
    parseAs: 'text',
    cache: 'no-store',
  });

  const body = response.data ?? resolveRssBody('error' in response ? response.error : undefined);
  const contentType =
    response.response?.headers.get('content-type') ?? 'application/rss+xml; charset=utf-8';

  return {
    status: response.response?.status ?? 502,
    body,
    contentType,
  };
}
