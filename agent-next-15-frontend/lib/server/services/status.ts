'use server';

import { getPlatformStatusApiV1StatusGet } from '@/lib/api/client/sdk.gen';
import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';
import { createApiClient } from '@/lib/server/apiClient';

/**
 * Fetch the latest platform status snapshot from the FastAPI backend.
 */
export async function fetchPlatformStatusSnapshot(): Promise<PlatformStatusResponse> {
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
