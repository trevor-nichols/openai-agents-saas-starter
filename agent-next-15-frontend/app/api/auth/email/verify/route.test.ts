import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const verifyEmailToken = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/email', () => ({
  verifyEmailToken,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/email/verify route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns success payload', async () => {
    const responsePayload: SuccessResponse = {
      success: true,
      message: 'verified',
      data: null,
    };
    verifyEmailToken.mockResolvedValueOnce(responsePayload);

    const request = buildRequest({ token: 'abc' });
    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(verifyEmailToken).toHaveBeenCalledWith({ token: 'abc' });
  });

  it('returns 401 when backend reports missing token', async () => {
    verifyEmailToken.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ token: 'abc' }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

