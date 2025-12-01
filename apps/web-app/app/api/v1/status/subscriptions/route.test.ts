import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { GET } from './route';

const listStatusSubscriptions = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/statusSubscriptions', () => ({
  listStatusSubscriptions,
}));

vi.mock('@/lib/auth/cookies', () => ({
  getSessionMetaFromCookies,
}));

const DEFAULT_SESSION = {
  userId: 'operator-1',
  tenantId: 'tenant-1',
  scopes: ['status:manage'],
  expiresAt: '2030-01-01T00:00:00.000Z',
  refreshExpiresAt: '2030-01-08T00:00:00.000Z',
};

const buildRequest = (url: string): NextRequest =>
  ({
    url,
  }) as unknown as NextRequest;

describe('GET /api/status/subscriptions', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
    listStatusSubscriptions.mockResolvedValue({
      items: [
        {
          id: 'sub-1',
          channel: 'email',
          severity_filter: 'major',
          status: 'active',
          target_masked: 'ops@example.com',
          tenant_id: 'tenant-1',
          created_by: 'ops',
          created_at: '2025-11-19T00:00:00Z',
          updated_at: '2025-11-19T00:00:00Z',
        },
      ],
      next_cursor: null,
    });
  });

  it('returns 200 with items when scope is present', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions?limit=5'));

    expect(response.status).toBe(200);
    const body = await response.json();
    expect(body.success).toBe(true);
    expect(body.items).toHaveLength(1);
    expect(listStatusSubscriptions).toHaveBeenCalledWith({
      cursor: null,
      tenantId: 'tenant-1',
      limit: 5,
      includeAllTenants: false,
    });
  });

  it('returns 401 when access token is missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce(null);

    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions'));

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Missing access token.' });
  });

  it('returns 403 when scope is absent', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce({
      ...DEFAULT_SESSION,
      scopes: ['conversations:read'],
    });

    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions'));

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Forbidden: status:manage scope required.',
    });
  });

  it('returns 400 when limit is invalid', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions?limit=abc'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'limit must be a positive integer.',
    });
  });

  it('supports global scope when tenant_id=all', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions?tenant_id=all'));

    expect(response.status).toBe(200);
    await response.json();
    expect(listStatusSubscriptions).toHaveBeenCalledWith({
      cursor: null,
      tenantId: null,
      limit: 25,
      includeAllTenants: true,
    });
  });

  it('falls back to session tenant when tenant_id missing', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions'));

    expect(response.status).toBe(200);
    await response.json();
    expect(listStatusSubscriptions).toHaveBeenCalledWith({
      cursor: null,
      tenantId: 'tenant-1',
      limit: 25,
      includeAllTenants: false,
    });
  });

  it('returns 400 for empty tenant_id', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions?tenant_id='));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'tenant_id must be a valid UUID or "all".',
    });
  });

  it('returns 400 for invalid tenant_id', async () => {
    const response = await GET(buildRequest('https://acme.test/api/status/subscriptions?tenant_id=not-a-uuid'));

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'tenant_id must be a valid UUID or "all".',
    });
  });
});
