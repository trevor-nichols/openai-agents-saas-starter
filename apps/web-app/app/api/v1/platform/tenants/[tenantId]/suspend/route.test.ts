import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { POST } from './route';

const suspendPlatformTenant = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/platformTenants', () => ({
  suspendPlatformTenant,
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

const buildRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    json: vi.fn(),
    headers: new Headers(),
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/platform/tenants/[tenantId]/suspend route', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
  });

  it('suspends tenant with reason', async () => {
    suspendPlatformTenant.mockResolvedValueOnce({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme',
      status: 'suspended',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-02T00:00:00Z',
      statusUpdatedAt: '2025-12-02T00:00:00Z',
      suspendedAt: '2025-12-02T00:00:00Z',
      deprovisionedAt: null,
      statusReason: 'policy',
      statusUpdatedBy: 'operator-1',
    });

    const request = buildRequest({
      json: vi.fn().mockResolvedValue({ reason: 'policy' }),
    });

    const response = await POST(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ status: 'suspended' });
  });

  it('returns 400 when reason missing', async () => {
    const request = buildRequest({
      json: vi.fn().mockResolvedValue({}),
    });

    const response = await POST(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'reason is required.' });
  });

  it('returns 401 when session missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce(null);

    const request = buildRequest({
      json: vi.fn().mockResolvedValue({ reason: 'policy' }),
    });

    const response = await POST(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Missing access token.' });
  });
});
