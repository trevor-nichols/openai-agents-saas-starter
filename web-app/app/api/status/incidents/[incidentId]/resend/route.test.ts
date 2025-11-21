import { vi } from 'vitest';

import type { NextRequest } from 'next/server';
import { POST } from './route';

const resendStatusIncident = vi.hoisted(() => vi.fn());
const getSessionMetaFromCookies = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/statusSubscriptions', () => ({
  resendStatusIncident,
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

const buildRequest = (payload: unknown): NextRequest =>
  ({
    json: vi.fn().mockResolvedValue(payload),
  }) as unknown as NextRequest;

describe('POST /api/status/incidents/[incidentId]/resend', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    getSessionMetaFromCookies.mockResolvedValue(DEFAULT_SESSION);
    resendStatusIncident.mockResolvedValue({ dispatched: 3 });
  });

  it('returns 202 when dispatch succeeds', async () => {
    const response = await POST(
      buildRequest({ severity: 'major', tenant_id: 'tenant-1' }),
      { params: { incidentId: 'inc-1' } },
    );

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual({ success: true, dispatched: 3 });
    expect(resendStatusIncident).toHaveBeenCalledWith('inc-1', {
      severity: 'major',
      tenant_id: 'tenant-1',
    });
  });

  it('returns 401 when session is missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce(null);

    const response = await POST(buildRequest({ severity: 'all' }), { params: { incidentId: 'inc-1' } });

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Missing access token.' });
  });

  it('returns 403 when scope is missing', async () => {
    getSessionMetaFromCookies.mockResolvedValueOnce({
      ...DEFAULT_SESSION,
      scopes: ['conversations:read'],
    });

    const response = await POST(buildRequest({ severity: 'all' }), { params: { incidentId: 'inc-1' } });

    expect(response.status).toBe(403);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Forbidden: status:manage scope required.',
    });
  });

  it('returns 422 for invalid payload', async () => {
    const response = await POST(buildRequest({ severity: 'low' }), { params: { incidentId: 'inc-1' } });

    expect(response.status).toBe(422);
    const body = await response.json();
    expect(body.success).toBe(false);
    expect(body.error).toBe('Invalid payload.');
  });

  it('maps not found errors to 404', async () => {
    resendStatusIncident.mockRejectedValueOnce(new Error('Not found'));

    const response = await POST(buildRequest({ severity: 'major' }), { params: { incidentId: 'missing' } });

    expect(response.status).toBe(404);
    await expect(response.json()).resolves.toEqual({ success: false, error: 'Not found' });
  });
});
