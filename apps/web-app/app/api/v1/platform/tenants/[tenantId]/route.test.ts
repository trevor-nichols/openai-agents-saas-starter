import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { GET, PATCH } from './route';

const getPlatformTenant = vi.hoisted(() => vi.fn());
const updatePlatformTenant = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/platformTenants', () => ({
  getPlatformTenant,
  updatePlatformTenant,
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
  scopes: ['support:*'],
  expiresAt: '2030-01-01T00:00:00.000Z',
  refreshExpiresAt: '2030-01-08T00:00:00.000Z',
};

const buildRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/platform/tenants/[tenantId] route', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
    getPlatformTenant.mockResolvedValue({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-01T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
      statusReason: null,
      statusUpdatedBy: null,
    });
  });

  it('returns tenant detail on GET', async () => {
    const response = await GET(buildRequest(), { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ id: 'tenant-1', slug: 'acme' });
  });

  it('updates tenant on PATCH', async () => {
    updatePlatformTenant.mockResolvedValueOnce({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme Labs',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-02T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
      statusReason: null,
      statusUpdatedBy: null,
    });

    const request = buildRequest({
      json: vi.fn().mockResolvedValue({ name: 'Acme Labs' }),
    });

    const response = await PATCH(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ name: 'Acme Labs' });
  });
});
