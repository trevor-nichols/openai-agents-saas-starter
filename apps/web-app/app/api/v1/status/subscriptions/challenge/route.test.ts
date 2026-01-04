import { vi } from 'vitest';

import { POST } from './route';

const confirmStatusSubscriptionChallenge = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/statusSubscriptions', () => ({
  confirmStatusSubscriptionChallenge,
}));

describe('/api/v1/status/subscriptions/challenge route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns backend response on success', async () => {
    const payload = { success: true, challenge: 'ok' };
    confirmStatusSubscriptionChallenge.mockResolvedValueOnce({
      data: payload,
      status: 202,
    });

    const request = { json: vi.fn().mockResolvedValue({ challenge: 'x' }) } as unknown as Request;

    const response = await POST(request);

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('maps missing token errors', async () => {
    confirmStatusSubscriptionChallenge.mockRejectedValueOnce(new Error('Missing access token'));
    const request = { json: vi.fn().mockResolvedValue({ challenge: 'x' }) } as unknown as Request;
    const response = await POST(request);
    expect(response.status).toBe(401);
  });
});
