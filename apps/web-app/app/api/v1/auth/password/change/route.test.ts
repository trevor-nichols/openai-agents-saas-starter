import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessNoDataResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const changePassword = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/passwords', () => ({
  changePassword,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/password/change route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 200 with success payload', async () => {
    const payload: SuccessNoDataResponse = {
      success: true,
      message: 'updated',
      data: null,
    };
    changePassword.mockResolvedValueOnce(payload);

    const response = await POST(
      buildRequest({ current_password: 'OldPassword123!', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when access token missing', async () => {
    changePassword.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(
      buildRequest({ current_password: 'OldPassword123!', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
