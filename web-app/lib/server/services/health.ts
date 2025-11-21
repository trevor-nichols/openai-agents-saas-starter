'use server';

import { getPlatformStatusApiV1StatusGet } from '@/lib/api/client/sdk.gen';
import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';

import { createApiClient } from '../apiClient';

async function fetchPlatformStatus(): Promise<PlatformStatusResponse> {
  const response = await getPlatformStatusApiV1StatusGet({
    client: createApiClient(),
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data as PlatformStatusResponse | undefined;
  if (!payload) {
    throw new Error('Platform status endpoint returned an empty payload.');
  }

  return payload;
}

/**
 * Retrieve the latest platform status snapshot. Used for public marketing surfaces.
 */
export async function getHealthStatus(): Promise<PlatformStatusResponse> {
  return fetchPlatformStatus();
}

/**
 * Reuse the platform status snapshot for readiness probes until a dedicated
 * readiness document is reintroduced into the spec.
 */
export async function getReadinessStatus(): Promise<PlatformStatusResponse> {
  return fetchPlatformStatus();
}
