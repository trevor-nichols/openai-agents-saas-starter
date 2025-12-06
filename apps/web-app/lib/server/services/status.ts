'use server';

import { cacheLife, cacheTag } from 'next/cache';

import { getPlatformStatusApiV1StatusGet } from '@/lib/api/client/sdk.gen';
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
