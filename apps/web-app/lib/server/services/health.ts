import 'server-only';

import { API_BASE_URL } from '@/lib/config/server';

type HealthResponse = Record<string, unknown> & { status?: string };

const BASE = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

async function fetchJson(path: string): Promise<HealthResponse> {
  const response = await fetch(`${BASE}${path}`, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`Health request failed (${response.status})`);
  }
  const payload = (await response.json()) as HealthResponse | null;
  if (!payload) {
    throw new Error('Health endpoint returned an empty payload.');
  }
  return payload;
}

/** Liveness probe – exercises FastAPI /health. */
export async function getHealthStatus(): Promise<HealthResponse> {
  return fetchJson('/health');
}

/** Readiness probe – exercises FastAPI /health/ready (includes DB check). */
export async function getReadinessStatus(): Promise<HealthResponse> {
  return fetchJson('/health/ready');
}

/** Storage probe – exercises FastAPI /health/storage. */
export async function getStorageHealthStatus(): Promise<HealthResponse> {
  return fetchJson('/health/storage');
}
