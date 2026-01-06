import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { FeatureFlags } from '@/types/features';

const getBackendFeatureFlags = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/features', async () => {
  const actual = await vi.importActual<typeof import('@/lib/server/features')>(
    '@/lib/server/features',
  );
  return {
    ...actual,
    getBackendFeatureFlags,
  };
});

async function loadHandler() {
  vi.resetModules();
  return import('./route');
}

async function buildApiError(status: number, message: string): Promise<Error> {
  const actual = await vi.importActual<typeof import('@/lib/server/features')>(
    '@/lib/server/features',
  );
  return new actual.FeatureFlagsApiError(status, message);
}

beforeEach(() => {
  getBackendFeatureFlags.mockReset();
});

describe('GET /api/v1/features', () => {
  it('returns backend feature flags on success', async () => {
    const payload: FeatureFlags = { billingEnabled: true, billingStreamEnabled: false };
    getBackendFeatureFlags.mockResolvedValueOnce(payload);

    const { GET } = await loadHandler();
    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 502 when backend flags fetch fails', async () => {
    getBackendFeatureFlags.mockRejectedValueOnce(new Error('boom'));

    const { GET } = await loadHandler();
    const response = await GET();

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'FeatureFlagsError',
      message: 'boom',
    });
  });

  it('returns 401 when auth is missing', async () => {
    getBackendFeatureFlags.mockRejectedValueOnce(
      await buildApiError(401, 'Missing access token'),
    );

    const { GET } = await loadHandler();
    const response = await GET();

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'FeatureFlagsError',
      message: 'Missing access token',
    });
  });

  it('returns 403 when auth is forbidden', async () => {
    getBackendFeatureFlags.mockRejectedValueOnce(
      await buildApiError(403, 'Tenant account is suspended.'),
    );

    const { GET } = await loadHandler();
    const response = await GET();

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'FeatureFlagsError',
      message: 'Tenant account is suspended.',
    });
  });
});
