import { vi } from 'vitest';

import type { HealthResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const getReadinessStatus = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/health', () => ({
  getReadinessStatus,
}));

describe('/api/health/ready route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns the backend readiness payload on success', async () => {
    const payload: HealthResponse = {
      status: 'ok',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      uptime: 42,
    };
    getReadinessStatus.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getReadinessStatus).toHaveBeenCalledTimes(1);
  });

  it('returns 503 when the readiness service throws', async () => {
    getReadinessStatus.mockRejectedValueOnce(new Error('boom'));

    const response = await GET();

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ message: 'boom' });
    expect(getReadinessStatus).toHaveBeenCalledTimes(1);
  });
});

