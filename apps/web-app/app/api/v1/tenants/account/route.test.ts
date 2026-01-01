import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { GET, PATCH } from './route';

const getTenantAccountFromApi = vi.hoisted(() => vi.fn());
const updateTenantAccountInApi = vi.hoisted(() => vi.fn());
const TenantAccountApiError = vi.hoisted(
  () =>
    class TenantAccountApiError extends Error {
      status: number;
      constructor(status: number, message: string) {
        super(message);
        this.status = status;
      }
    },
);

vi.mock('@/lib/server/services/tenantAccount', () => ({
  getTenantAccountFromApi,
  updateTenantAccountInApi,
  TenantAccountApiError,
}));

const mockRequest = (overrides: Partial<NextRequest> = {}): NextRequest =>
  ({
    headers: new Headers(),
    json: vi.fn(),
    ...overrides,
  }) as unknown as NextRequest;

describe('/api/v1/tenants/account route', () => {
  afterEach(() => {
    vi.resetAllMocks();
  });

  it('returns tenant account payload on GET', async () => {
    const headers = new Headers({
      'x-tenant-role': 'member',
      'x-tenant-id': 'tenant-override',
      'x-operator-override': 'true',
      'x-operator-reason': 'storybook',
    });

    getTenantAccountFromApi.mockResolvedValueOnce({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-02T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
    });

    const response = await GET(mockRequest({ headers }));

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-02T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
    });

    expect(getTenantAccountFromApi).toHaveBeenCalledWith({ tenantRole: 'member' });
  });

  it('updates tenant account on PATCH', async () => {
    const headers = new Headers({
      'x-tenant-role': 'admin',
      'x-operator-override': 'true',
      'x-operator-reason': 'manual',
    });

    updateTenantAccountInApi.mockResolvedValueOnce({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme Labs',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-03T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
    });

    const request = mockRequest({
      headers,
      json: vi.fn().mockResolvedValue({ name: 'Acme Labs' }),
    });

    const response = await PATCH(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual({
      id: 'tenant-1',
      slug: 'acme',
      name: 'Acme Labs',
      status: 'active',
      createdAt: '2025-12-01T00:00:00Z',
      updatedAt: '2025-12-03T00:00:00Z',
      statusUpdatedAt: null,
      suspendedAt: null,
      deprovisionedAt: null,
    });

    expect(updateTenantAccountInApi).toHaveBeenCalledWith(
      { name: 'Acme Labs' },
      { tenantRole: 'admin' },
    );
  });

  it('returns 401 when auth is missing on GET', async () => {
    getTenantAccountFromApi.mockRejectedValueOnce(new Error('Missing access token.'));

    const response = await GET(mockRequest());

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token.' });
  });

  it('returns 403 when API forbids PATCH', async () => {
    updateTenantAccountInApi.mockRejectedValueOnce(new TenantAccountApiError(403, 'Forbidden'));

    const request = mockRequest({
      json: vi.fn().mockResolvedValue({ name: 'Acme Labs' }),
    });

    const response = await PATCH(request);

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({ message: 'Forbidden' });
  });

  it('validates payload on PATCH', async () => {
    const request = mockRequest({
      json: vi.fn().mockResolvedValue({}),
    });

    const response = await PATCH(request);

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({ message: 'name is required.' });
  });
});
