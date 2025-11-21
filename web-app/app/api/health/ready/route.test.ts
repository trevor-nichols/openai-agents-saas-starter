import { vi } from 'vitest';

import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';

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
    const payload: PlatformStatusResponse = {
      generated_at: new Date().toISOString(),
      overview: {
        state: 'operational',
        description: 'Ready for traffic',
        updated_at: new Date().toISOString(),
      },
      services: [],
      incidents: [],
      uptime_metrics: [],
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
