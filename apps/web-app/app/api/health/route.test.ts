import { vi } from 'vitest';

import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';

import { GET } from './route';

const getHealthStatus = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/health', () => ({
  getHealthStatus,
}));

describe('/api/health route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns the backend health payload on success', async () => {
    const payload: PlatformStatusResponse = {
      generated_at: new Date().toISOString(),
      overview: {
        state: 'operational',
        description: 'All systems nominal',
        updated_at: new Date().toISOString(),
      },
      services: [],
      incidents: [],
      uptime_metrics: [],
    };
    getHealthStatus.mockResolvedValueOnce(payload);

    const response = await GET();

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
    expect(getHealthStatus).toHaveBeenCalledTimes(1);
  });

  it('returns 503 when the health service throws', async () => {
    getHealthStatus.mockRejectedValueOnce(new Error('boom'));

    const response = await GET();

    expect(response.status).toBe(503);
    await expect(response.json()).resolves.toEqual({ message: 'boom' });
    expect(getHealthStatus).toHaveBeenCalledTimes(1);
  });
});
