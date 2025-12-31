import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { POST } from './route';

const deprovisionPlatformTenant = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/platformTenants', () => ({
  deprovisionPlatformTenant,
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

describe('/api/v1/platform/tenants/[tenantId]/deprovision route', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
  });

  it('deprovisions tenant with reason', async () => {
    deprovisionPlatformTenant.mockResolvedValueOnce({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme',
      status: 'deprovisioned',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-04T00:00:00Z',
      statusUpdatedAt: '2025-12-04T00:00:00Z',
      suspendedAt: null,
      deprovisionedAt: '2025-12-04T00:00:00Z',
      statusReason: 'contract ended',
      statusUpdatedBy: 'operator-1',
    });

    const request = buildRequest({
      json: vi.fn().mockResolvedValue({ reason: 'contract ended' }),
    });

    const response = await POST(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toMatchObject({ status: 'deprovisioned' });
  });

  it('returns 400 when reason missing', async () => {
    const request = buildRequest({
      json: vi.fn().mockResolvedValue({}),
    });

    const response = await POST(request, { params: { tenantId: 'tenant-1' } });

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'reason is required.' });
  });
});
