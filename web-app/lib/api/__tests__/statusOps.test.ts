import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { fetchStatusSubscriptions, resendIncident } from '../statusOps';

const originalFetch = global.fetch;

describe('status ops API helpers', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
  });

  it('fetchStatusSubscriptions maps response payload', async () => {
    const payload = {
      success: true,
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
      next_cursor: '15',
    };

    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await fetchStatusSubscriptions({ limit: 10, cursor: '5', tenantId: 'tenant-1' });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/status/subscriptions?limit=10&cursor=5&tenant_id=tenant-1',
      expect.objectContaining({ cache: 'no-store' }),
    );
    expect(result.items[0]).toMatchObject({
      id: 'sub-1',
      channel: 'email',
      severityFilter: 'major',
      tenantId: 'tenant-1',
    });
    expect(result.nextCursor).toBe('15');
  });

  it('fetchStatusSubscriptions throws when success is false', async () => {
    const payload = { success: false, error: 'nope' };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(fetchStatusSubscriptions()).rejects.toThrow('nope');
  });

  it('resendIncident returns dispatched count', async () => {
    const payload = { success: true, dispatched: 7 };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 202,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    const result = await resendIncident({ incidentId: 'inc-1', severity: 'all', tenantId: null });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/status/incidents/inc-1/resend',
      expect.objectContaining({
        method: 'POST',
      }),
    );
    expect(result.dispatched).toBe(7);
  });

  it('resendIncident throws when response is not ok', async () => {
    const payload = { success: false, error: 'forbidden' };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 403,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await expect(resendIncident({ incidentId: 'inc-1' })).rejects.toThrow('forbidden');
  });
});

describe('status ops API helpers - global scope', () => {
  afterEach(() => {
    if (originalFetch) {
      global.fetch = originalFetch;
    } else {
      // @ts-expect-error - cleaning up mocked fetch reference
      delete global.fetch;
    }
  });

  it('sends tenant_id=all when tenantId is null', async () => {
    const payload = { success: true, items: [], next_cursor: null };
    global.fetch = vi.fn().mockResolvedValue(
      new Response(JSON.stringify(payload), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );

    await fetchStatusSubscriptions({ tenantId: null });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/status/subscriptions?tenant_id=all',
      expect.anything(),
    );
  });
});
