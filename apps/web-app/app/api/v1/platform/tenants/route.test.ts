import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { GET, POST } from './route';

const listPlatformTenants = vi.hoisted(() => vi.fn());
const createPlatformTenant = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/platformTenants', () => ({
  listPlatformTenants,
  createPlatformTenant,
  PlatformTenantsApiError: class PlatformTenantsApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
      super(message);
      this.status = status;
    }
  },
}));

vi.mock('@/lib/auth/cookies', () => ({
  getSessionMetaFromCookies,
}));

const DEFAULT_SESSION = {
  userId: 'operator-1',
  tenantId: 'tenant-1',
  scopes: ['platform:operator'],
  expiresAt: '2030-01-01T00:00:00.000Z',
  refreshExpiresAt: '2030-01-08T00:00:00.000Z',
};

const buildRequest = (url: string, overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    url,
    json: vi.fn(),
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/platform/tenants route', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
    listPlatformTenants.mockResolvedValue({
      accounts: [],
      total: 0,
    });
  });

  it('returns 200 with tenant list', async () => {
    const response = await GET(buildRequest('https://acme.test/api/v1/platform/tenants'));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({ accounts: [], total: 0 });
  });

  it('returns 400 for invalid limit', async () => {
    const response = await GET(buildRequest('https://acme.test/api/v1/platform/tenants?limit=bad'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'limit must be a positive integer.',
    });
  });

  it('returns 401 when session missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce(null);
    const response = await GET(buildRequest('https://acme.test/api/v1/platform/tenants'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Missing access token.' });
  });

  it('returns 403 when scope missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce({
      ...DEFAULT_SESSION,
      scopes: ['status:manage'],
    });

    const response = await GET(buildRequest('https://acme.test/api/v1/platform/tenants'));

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Forbidden: operator scope required.',
    });
  });

  it('creates tenant on POST', async () => {
    createPlatformTenant.mockResolvedValueOnce({
      id: 'tenant-2',
      slug: 'beta',
      name: 'Beta',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-01T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
      statusReason: null,
      statusUpdatedBy: null,
    });

    const response = await POST(
      buildRequest('https://acme.test/api/v1/platform/tenants', {
        json: vi.fn().mockResolvedValue({ name: 'Beta', slug: 'beta' }),
      }),
    );

    expect(response.status).toBe(201);
    await expect(response.json()).resolves.toMatchObject({ name: 'Beta', slug: 'beta' });
  });
});
