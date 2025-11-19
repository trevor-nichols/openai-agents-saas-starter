'use server';

import { healthCheckHealthGet, readinessCheckHealthReadyGet } from '@/lib/api/client/sdk.gen';
import type { HealthResponse } from '@/lib/api/client/types.gen';

import { createApiClient } from '../apiClient';

/**
 * Retrieve the backend liveness payload.
 */
export async function getHealthStatus(): Promise<HealthResponse> {
  const response = await healthCheckHealthGet({
    client: createApiClient(),
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data as HealthResponse | undefined;
  if (!payload) {
    throw new Error('Health endpoint returned an empty payload.');
  }

  return payload;
}

/**
 * Retrieve the backend readiness payload.
 */
export async function getReadinessStatus(): Promise<HealthResponse> {
  const response = await readinessCheckHealthReadyGet({
    client: createApiClient(),
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data as HealthResponse | undefined;
  if (!payload) {
    throw new Error('Readiness endpoint returned an empty payload.');
  }

  return payload;
}

