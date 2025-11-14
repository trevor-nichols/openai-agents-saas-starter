import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const requestPasswordReset = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/passwords', () => ({
  requestPasswordReset,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/password/forgot route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 202 with success payload', async () => {
    const payload: SuccessResponse = {
      success: true,
      message: 'queued',
      data: null,
    };
    requestPasswordReset.mockResolvedValueOnce(payload);

    const response = await POST(buildRequest({ email: 'user@example.com' }));

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when access token missing', async () => {
    requestPasswordReset.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ email: 'user@example.com' }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

