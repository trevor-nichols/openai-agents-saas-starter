import { vi } from 'vitest';

import { GET } from './route';

const getStorageHealthStatus = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/health', () => ({
  getStorageHealthStatus,
}));

describe('/api/health/storage route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns storage health payload on success', async () => {
    const payload = { ok: true, provider: 's3' };
    getStorageHealthStatus.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getStorageHealthStatus).toHaveBeenCalledTimes(1);
  });

  it('returns 503 on failure', async () => {
    getStorageHealthStatus.mockRejectedValueOnce(new Error('storage down'));

    const response = await GET();

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ message: 'storage down' });
  });
});
