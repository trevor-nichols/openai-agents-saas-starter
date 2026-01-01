import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { GET } from './route';

const listSsoProvidersApiV1AuthSsoProvidersGet = vi.hoisted(() => vi.fn());

vi.mock('@/lib/api/client/sdk.gen', () => ({
  listSsoProvidersApiV1AuthSsoProvidersGet,
}));

vi.mock('@/lib/server/apiClient', () => ({
  createApiClient: () => ({}),
}));

describe('GET /api/v1/auth/sso/providers', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns 400 when tenant selector is missing', async () => {
    const request = { url: 'http://localhost/api/v1/auth/sso/providers' } as NextRequest;
    const response = await GET(request);

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toMatchObject({
      message: 'tenant_id or tenant_slug is required.',
    });
    expect(listSsoProvidersApiV1AuthSsoProvidersGet).not.toHaveBeenCalled();
  });

  it('returns 409 when tenant_id and tenant_slug are both provided', async () => {
    const request = {
      url: 'http://localhost/api/v1/auth/sso/providers?tenant_id=1&tenant_slug=acme',
    } as NextRequest;

    const response = await GET(request);

    expect(response.status).toBe(409);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Provide either tenant_id or tenant_slug, not both.',
    });
    expect(listSsoProvidersApiV1AuthSsoProvidersGet).not.toHaveBeenCalled();
  });

  it('returns providers when backend responds', async () => {
    listSsoProvidersApiV1AuthSsoProvidersGet.mockResolvedValue({
      data: { providers: [{ provider_key: 'google', display_name: 'Google' }] },
    });

    const request = {
      url: 'http://localhost/api/v1/auth/sso/providers?tenant_slug=acme',
    } as NextRequest;

    const response = await GET(request);

    expect(listSsoProvidersApiV1AuthSsoProvidersGet).toHaveBeenCalledWith(
      expect.objectContaining({
        query: { tenant_id: undefined, tenant_slug: 'acme' },
        throwOnError: true,
      }),
    );
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      providers: [{ provider_key: 'google', display_name: 'Google' }],
    });
  });

  it('surfaces backend errors', async () => {
    listSsoProvidersApiV1AuthSsoProvidersGet.mockRejectedValue({
      status: 404,
      detail: 'Tenant not found',
      message: 'Tenant not found',
    });

    const request = {
      url: 'http://localhost/api/v1/auth/sso/providers?tenant_id=missing',
    } as NextRequest;

    const response = await GET(request);

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toMatchObject({
      message: 'Tenant not found',
      detail: 'Tenant not found',
    });
  });
});
