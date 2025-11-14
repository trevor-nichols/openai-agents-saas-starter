import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { UserRegisterResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const registerTenant = vi.hoisted(() => vi.fn());
const persistSessionCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/signup', () => ({
  registerTenant,
}));

vi.mock('@/lib/auth/cookies', () => ({
  persistSessionCookies,
}));

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('/api/auth/register route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns 201 with registration payload and persists cookies', async () => {
    const responsePayload: UserRegisterResponse = {
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
      expires_at: new Date().toISOString(),
      refresh_expires_at: new Date().toISOString(),
      kid: 'kid',
      refresh_kid: 'rid',
      scopes: ['read'],
      tenant_id: 'tenant',
      user_id: 'user',
      email_verified: true,
      session_id: 'session',
      tenant_slug: 'tenant',
    };
    registerTenant.mockResolvedValueOnce(responsePayload);

    const response = await POST(
      buildRequest({ email: 'owner@example.com', password: 'Password123!', tenant_name: 'Example' }),
    );

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(persistSessionCookies).toHaveBeenCalledWith({
      access_token: 'access',
      refresh_token: 'refresh',
      token_type: 'bearer',
      expires_at: responsePayload.expires_at,
      refresh_expires_at: responsePayload.refresh_expires_at,
      kid: 'kid',
      refresh_kid: 'rid',
      scopes: ['read'],
      tenant_id: 'tenant',
      user_id: 'user',
    });
  });

  it('returns 400 when backend reports invalid data', async () => {
    registerTenant.mockRejectedValueOnce(new Error('Invalid password'));

    const response = await POST(
      buildRequest({ email: 'owner@example.com', password: 'weak', tenant_name: 'Example' }),
    );

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'Invalid password' });
  });
});

