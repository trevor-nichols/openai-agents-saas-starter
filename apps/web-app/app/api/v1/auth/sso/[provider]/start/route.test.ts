import { vi } from 'vitest';

import { POST } from './route';

const startSsoApiV1AuthSsoProviderStartPost = vi.hoisted(() => vi.fn());
const clearSsoRedirectCookie = vi.hoisted(() => vi.fn());
const setSsoRedirectCookie = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client/sdk.gen', () => ({
  startSsoApiV1AuthSsoProviderStartPost,
}));

vi.mock('@/lib/auth/ssoCookies', () => ({
  clearSsoRedirectCookie,
  setSsoRedirectCookie,
}));

vi.mock('@/lib/server/apiClient', () => ({
  createApiClient: () => ({}),
}));

describe('POST /api/v1/auth/sso/[provider]/start', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when tenant selector is missing', async () => {
    const request = new Request('http://localhost/api/v1/auth/sso/google/start', {
      method: 'POST',
      body: JSON.stringify({}),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      message: 'tenant_id or tenant_slug is required.',
    });
  });

  it('returns 409 when tenant_id and tenant_slug are both provided', async () => {
    const request = new Request('http://localhost/api/v1/auth/sso/google/start', {
      method: 'POST',
      body: JSON.stringify({ tenant_id: '1', tenant_slug: 'acme' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(409);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Provide either tenant_id or tenant_slug, not both.',
    });
  });

  it('returns 400 for invalid redirect targets', async () => {
    const request = new Request('http://localhost/api/v1/auth/sso/google/start', {
      method: 'POST',
      body: JSON.stringify({ tenant_slug: 'acme', redirect_to: 'https://example.com' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Invalid redirect target.',
    });
    expect(startSsoApiV1AuthSsoProviderStartPost).not.toHaveBeenCalled();
  });

  it('starts SSO and stores redirect cookie', async () => {
    startSsoApiV1AuthSsoProviderStartPost.mockResolvedValue({
      data: { authorize_url: 'https://accounts.google.com' },
    });

    const request = new Request('http://localhost/api/v1/auth/sso/google/start', {
      method: 'POST',
      body: JSON.stringify({
        tenant_slug: 'acme',
        login_hint: 'user@example.com',
        redirect_to: '/dashboard',
      }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(startSsoApiV1AuthSsoProviderStartPost).toHaveBeenCalledWith(
      expect.objectContaining({
        path: { provider: 'google' },
        body: {
          tenant_id: null,
          tenant_slug: 'acme',
          login_hint: 'user@example.com',
        },
      }),
    );
    expect(setSsoRedirectCookie).toHaveBeenCalledWith('/dashboard');
    expect(clearSsoRedirectCookie).not.toHaveBeenCalled();
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      authorize_url: 'https://accounts.google.com',
    });
  });

  it('clears redirect cookie when redirect_to is omitted', async () => {
    startSsoApiV1AuthSsoProviderStartPost.mockResolvedValue({
      data: { authorize_url: 'https://accounts.google.com' },
    });

    const request = new Request('http://localhost/api/v1/auth/sso/google/start', {
      method: 'POST',
      body: JSON.stringify({ tenant_slug: 'acme' }),
      headers: { 'Content-Type': 'application/json' },
    });

    const response = await POST(request, { params: Promise.resolve({ provider: 'google' }) });

    expect(clearSsoRedirectCookie).toHaveBeenCalled();
    expect(setSsoRedirectCookie).not.toHaveBeenCalled();
    expect(response.status).toBe(200);
  });
});
