'use server';

import {
  healthCheckHealthGet,
  readinessCheckHealthReadyGet,
  storageHealthHealthStorageGet,
} from '@/lib/api/client/sdk.gen';
import type { HealthResponse } from '@/lib/api/client/types.gen';

import { createApiClient } from '../apiClient';

/**
 * Retrieve the API service liveness document.
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
 * Retrieve the API service readiness document.
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

/**
 * Retrieve storage provider health (informational).
 */
export async function getStorageHealthStatus(): Promise<unknown> {
  const response = await storageHealthHealthStorageGet({
    client: createApiClient(),
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Storage health endpoint returned an empty payload.');
  }

  return payload;
}
