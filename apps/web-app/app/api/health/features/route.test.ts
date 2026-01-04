import { vi } from 'vitest';

import { GET } from './route';

const getBackendFeatureFlags = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/features', () => ({
  getBackendFeatureFlags,
}));

describe('/api/health/features route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns backend feature flags on success', async () => {
    const payload = { billingEnabled: true, billingStreamEnabled: false };
    getBackendFeatureFlags.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getBackendFeatureFlags).toHaveBeenCalledTimes(1);
  });

  it('returns 502 when the backend feature fetch fails', async () => {
    getBackendFeatureFlags.mockRejectedValueOnce(new Error('backend down'));

    const response = await GET();

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({ message: 'backend down' });
    expect(getBackendFeatureFlags).toHaveBeenCalledTimes(1);
  });
});
