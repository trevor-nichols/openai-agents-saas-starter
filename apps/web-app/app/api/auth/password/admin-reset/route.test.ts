import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { SuccessResponse } from '@/lib/api/client/types.gen';
import { POST } from './route';

const adminResetPassword = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/passwords', () => ({
  adminResetPassword,
}));

vi.mock('@/lib/auth/cookies', () => ({
  getSessionMetaFromCookies,
}));

const DEFAULT_SESSION = {
  userId: 'admin-user',
  tenantId: 'tenant-1',
  scopes: ['support:read'],
  expiresAt: '2030-01-01T00:00:00.000Z',
  refreshExpiresAt: '2030-01-08T00:00:00.000Z',
};

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/password/admin-reset route', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
  });

  it('returns 200 with success payload', async () => {
    const payload: SuccessResponse = {
      success: true,
      message: 'reset',
      data: null,
    };

    adminResetPassword.mockResolvedValueOnce(payload);

    const response = await POST(
      buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(payload);
  });

  it('returns 401 when access token missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce(null);

    const response = await POST(buildRequest({ user_id: 'user-1', new_password: 'pass' }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token.' });
  });

  it('returns 403 when scope is absent', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce({
      ...DEFAULT_SESSION,
      scopes: ['conversations:read'],
    });

    const response = await POST(buildRequest({ user_id: 'user-1', new_password: 'pass' }));

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      message: 'Forbidden: support:read scope required.',
    });
  });

  it('returns 400 when tenant context missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce({
      ...DEFAULT_SESSION,
      tenantId: '',
    });

    const response = await POST(buildRequest({ user_id: 'user-1', new_password: 'pass' }));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      message: 'Tenant context is required for password reset.',
    });
  });

  it('maps not found errors to 404', async () => {
    adminResetPassword.mockRejectedValueOnce(new Error('Not found'));

    const response = await POST(
      buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ message: 'Not found' });
  });

  it('maps password policy errors to 400', async () => {
    adminResetPassword.mockRejectedValueOnce(new Error('Password policy violation'));

    const response = await POST(
      buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Password policy violation' });
  });

  it('maps validation errors to 422', async () => {
    adminResetPassword.mockRejectedValueOnce(new Error('Validation failed'));

    const response = await POST(
      buildRequest({ user_id: 'bad', new_password: 'short' }),
    );

    expect(response.status).toBe(422);
    const body = await response.json();
    expect(body.message).toBe('Invalid payload.');
    expect(body.issues).toBeDefined();
  });

  it('returns 422 with zod issues for malformed payload', async () => {
    const response = await POST(buildRequest({ user_id: '', new_password: 'short' }));

    expect(response.status).toBe(422);
    const body = await response.json();
    expect(body.message).toBe('Invalid payload.');
    expect(body.issues?.fieldErrors?.user_id).toBeDefined();
  });

  it('falls back to 500 for unexpected password messages', async () => {
    adminResetPassword.mockRejectedValueOnce(new Error('Admin password reset returned empty response.'));

    const response = await POST(
      buildRequest({ user_id: 'user-1', new_password: 'NewPassword123!' }),
    );

    expect(response.status).toBe(500);
    await expect(response.json()).resolves.toEqual({ message: 'Admin password reset returned empty response.' });
  });
});
