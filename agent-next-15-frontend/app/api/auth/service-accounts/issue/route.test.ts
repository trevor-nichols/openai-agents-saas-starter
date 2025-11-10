import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import type { ServiceAccountTokenResponse } from '@/lib/api/client/types.gen';

import { POST } from './route';

const issueServiceAccountToken = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/serviceAccounts', () => ({
  issueServiceAccountToken,
}));

const buildRequest = (payload: unknown, headers?: Record<string, string>): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
    headers: new Headers(headers),
  }) as unknown as NextRequest;

describe('/api/auth/service-accounts/issue route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns issued token payload', async () => {
    const responsePayload: ServiceAccountTokenResponse = {
      refresh_token: 'token',
      expires_at: new Date().toISOString(),
      issued_at: new Date().toISOString(),
      scopes: ['read'],
      tenant_id: null,
      kid: 'kid',
      account: 'service-account',
      token_use: 'refresh',
      session_id: null,
    };
    issueServiceAccountToken.mockResolvedValueOnce(responsePayload);

    const response = await POST(
      buildRequest({ account: 'service-account', scopes: ['read'] }, { 'x-vault-payload': 'vault' }),
    );

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toEqual(responsePayload);
    expect(issueServiceAccountToken).toHaveBeenCalledWith(
      { account: 'service-account', scopes: ['read'] },
      { vaultPayload: 'vault' },
    );
  });

  it('returns 401 when access token missing', async () => {
    issueServiceAccountToken.mockRejectedValueOnce(new Error('Missing access token'));

    const response = await POST(buildRequest({ account: 'service-account', scopes: ['read'] }));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});

