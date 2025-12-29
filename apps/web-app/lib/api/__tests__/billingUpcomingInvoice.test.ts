import { describe, expect, it, vi } from 'vitest';

import { previewUpcomingInvoice } from '../billingUpcomingInvoice';

describe('billingUpcomingInvoice helpers', () => {
  it('returns preview on success', async () => {
    const mockResponse = new Response(
      JSON.stringify({
        plan_code: 'starter',
        plan_name: 'Starter',
        seat_count: 3,
        amount_due_cents: 4900,
        currency: 'USD',
        period_start: '2025-12-01',
        period_end: '2025-12-31',
        lines: [],
      }),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    const preview = await previewUpcomingInvoice('tenant-1', {});

    expect(preview.plan_code).toBe('starter');
    fetchSpy.mockRestore();
  });

  it('throws billing disabled on 404 payload', async () => {
    const mockResponse = new Response(JSON.stringify({ message: 'Billing is disabled.' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    await expect(previewUpcomingInvoice('tenant-1', {})).rejects.toThrow('Billing is disabled.');
    fetchSpy.mockRestore();
  });
});
