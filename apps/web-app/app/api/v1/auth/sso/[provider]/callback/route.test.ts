import { vi } from 'vitest';

import { POST } from './route';

const completeSsoApiV1AuthSsoProviderCallbackPost = vi.hoisted(() => vi.fn());
const readSsoRedirectCookie = vi.hoisted(() => vi.fn());
const clearSsoRedirectCookie = vi.hoisted(() => vi.fn());
const persistSessionFromResponse = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client/sdk.gen', () => ({
  completeSsoApiV1AuthSsoProviderCallbackPost,
}));

vi.mock('@/lib/auth/ssoCookies', () => ({
  readSsoRedirectCookie,
  clearSsoRedirectCookie,
}));

vi.mock('@/lib/auth/session', () => ({
  persistSessionFromResponse,
}));

vi.mock('@/lib/server/apiClient', () => ({
  createApiClient: () => ({}),
}));

describe('POST /api/v1/auth/sso/[provider]/callback', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    readSsoRedirectCookie.mockResolvedValue('/dashboard');
  });

  it('returns 400 when code or state is missing', async () => {
    const request = new Request('http://localhost/api/v1/auth/sso/google/callback', {
      method: 'POST',
      body: JSON.stringify({ code: 'abc' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      message: 'code and state are required.',
    });
  });

  it('returns MFA challenge when required', async () => {
    completeSsoApiV1AuthSsoProviderCallbackPost.mockResolvedValue({
      data: { challenge_token: 'token', methods: [{ id: 'm1', method_type: 'totp' }] },
      response: { status: 202 },
    });

    const request = new Request('http://localhost/api/v1/auth/sso/google/callback', {
      method: 'POST',
      body: JSON.stringify({ code: 'abc', state: 'state' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toMatchObject({
      status: 'mfa_required',
      redirect_to: '/dashboard',
      mfa: { challenge_token: 'token' },
    });
    expect(persistSessionFromResponse).not.toHaveBeenCalled();
    expect(clearSsoRedirectCookie).toHaveBeenCalled();
  });

  it('persists session and returns redirect target on success', async () => {
    completeSsoApiV1AuthSsoProviderCallbackPost.mockResolvedValue({
      data: {
        access_token: 'access',
        refresh_token: 'refresh',
        expires_at: new Date().toISOString(),
        refresh_expires_at: new Date().toISOString(),
        kid: 'kid',
        refresh_kid: 'rkid',
        scopes: ['a'],
        tenant_id: 'tenant',
        user_id: 'user',
      },
    });

    const request = new Request('http://localhost/api/v1/auth/sso/google/callback', {
      method: 'POST',
      body: JSON.stringify({ code: 'abc', state: 'state' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(persistSessionFromResponse).toHaveBeenCalled();
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      status: 'authenticated',
      redirect_to: '/dashboard',
    });
    expect(clearSsoRedirectCookie).toHaveBeenCalled();
  });

  it('surfaces backend errors', async () => {
    completeSsoApiV1AuthSsoProviderCallbackPost.mockRejectedValue({
      status: 401,
      detail: 'Invalid code',
      message: 'Invalid code',
    });

    const request = new Request('http://localhost/api/v1/auth/sso/google/callback', {
      method: 'POST',
      body: JSON.stringify({ code: 'abc', state: 'state' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Invalid code',
      detail: 'Invalid code',
    });
  });
});
