import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const confirmPasswordReset = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/passwords', () => ({
  confirmPasswordReset,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/password/confirm route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 200 with success payload', async () => {
    const payload: SuccessResponse = {
      success: true,
      message: 'updated',
      data: null,
    };
    confirmPasswordReset.mockResolvedValueOnce(payload);

    const response = await POST(buildRequest({ token: 'abc', new_password: 'Password123!' }));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when access token missing', async () => {
    confirmPasswordReset.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ token: 'abc', new_password: 'Password123!' }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

