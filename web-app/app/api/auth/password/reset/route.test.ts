import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const adminResetPassword = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/passwords', () => ({
  adminResetPassword,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/password/reset route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 200 with success payload', async () => {
    const payload: SuccessResponse = {
      success: true,
      message: 'reset',
      data: null,
    };
    adminResetPassword.mockResolvedValueOnce(payload);

    const response = await POST(buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when access token missing', async () => {
    adminResetPassword.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

