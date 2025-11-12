'use server';

import { getPlatformStatusApiV1StatusGet } from '@/lib/api/client/sdk.gen';
import { createApiClient } from '@/lib/server/apiClient';
import type { RawPlatformStatusResponse } from '@/types/status';

/**
 * Fetch the latest platform status snapshot from the FastAPI backend.
 */
export async function fetchPlatformStatusSnapshot(): Promise<RawPlatformStatusResponse> {
  const client = createApiClient();

  return (await getPlatformStatusApiV1StatusGet({
    client,
    responseStyle: 'data',
    throwOnError: true,
  })) as unknown as RawPlatformStatusResponse;
}
