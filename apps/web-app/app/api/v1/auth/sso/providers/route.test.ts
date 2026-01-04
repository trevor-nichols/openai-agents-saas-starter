import { vi } from 'vitest';
import type { NextRequest } from 'next/server';

import { GET } from './route';

const listSsoProviders = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/auth/sso', () => ({
  listSsoProviders,
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
    expect(listSsoProviders).not.toHaveBeenCalled();
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
    expect(listSsoProviders).not.toHaveBeenCalled();
  });

  it('returns providers when backend responds', async () => {
    listSsoProviders.mockResolvedValue({
      providers: [{ provider_key: 'google', display_name: 'Google' }],
    });

    const request = {
      url: 'http://localhost/api/v1/auth/sso/providers?tenant_slug=acme',
    } as NextRequest;

    const response = await GET(request);

    expect(listSsoProviders).toHaveBeenCalledWith({
      tenantId: null,
      tenantSlug: 'acme',
    });
    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({
      providers: [{ provider_key: 'google', display_name: 'Google' }],
    });
  });

  it('surfaces backend errors', async () => {
    listSsoProviders.mockRejectedValue({
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
