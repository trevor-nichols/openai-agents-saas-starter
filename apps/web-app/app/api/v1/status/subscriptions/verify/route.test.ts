import { vi } from 'vitest';

import type { StatusSubscriptionResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const verifyStatusSubscriptionToken = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/statusSubscriptions', () => ({
  verifyStatusSubscriptionToken,
  StatusSubscriptionServiceError: class StatusSubscriptionServiceError extends Error {
    constructor(message: string, public status: number) {
      super(message);
      this.name = 'StatusSubscriptionServiceError';
    }
  },
}));

describe('/api/v1/status/subscriptions/verify route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when token missing', async () => {
    const request = { json: vi.fn().mockResolvedValue({}) } as unknown as Request;
    const response = await POST(request as never);
    expect(response.status).toBe(400);
  });

  it('returns payload on success', async () => {
    const payload: StatusSubscriptionResponse = {
      id: 'sub-1',
      status: 'verified',
      channel: 'email',
      severity_filter: 'all',
      target_masked: 't@example.com',
      created_by: 'user-1',
      created_at: '2025-12-01T00:00:00Z',
      updated_at: '2025-12-01T00:00:00Z',
    };
    verifyStatusSubscriptionToken.mockResolvedValueOnce(payload);
    const request = { json: vi.fn().mockResolvedValue({ token: 'abc' }) } as unknown as Request;

    const response = await POST(request as never);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('propagates service errors with status', async () => {
    const { StatusSubscriptionServiceError } = await import('@/lib/server/services/statusSubscriptions');
    const err = new StatusSubscriptionServiceError('bad', 403);
    verifyStatusSubscriptionToken.mockRejectedValueOnce(err);

    const request = { json: vi.fn().mockResolvedValue({ token: 'abc' }) } as unknown as Request;
    const response = await POST(request as never);

    expect(response.status).toBe(403);
  });
});
