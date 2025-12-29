import { describe, expect, it, vi } from 'vitest';

import { fetchBillingInvoice, fetchBillingInvoices } from '../billingInvoices';

describe('fetchBillingInvoices', () => {
  it('returns empty list when billing is disabled', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    const result = await fetchBillingInvoices({ tenantId: 't1' });

    expect(result).toEqual({ items: [], next_offset: null });
    fetchSpy.mockRestore();
  });

  it('returns invoice list payload', async () => {
    const payload = {
      items: [
        {
          invoice_id: 'in_123',
          status: 'paid',
          amount_cents: 1200,
          currency: 'USD',
          period_start: '2025-01-01T00:00:00Z',
          period_end: '2025-02-01T00:00:00Z',
          hosted_invoice_url: 'https://example.com/invoices/in_123',
          created_at: '2025-01-01T00:00:00Z',
        },
      ],
      next_offset: null,
    };

    const mockResponse = new Response(JSON.stringify(payload), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    const result = await fetchBillingInvoices({ tenantId: 't1', limit: 10, offset: 0 });

    expect(result).toEqual(payload);
    fetchSpy.mockRestore();
  });
});

describe('fetchBillingInvoice', () => {
  it('throws when billing is disabled', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(fetchBillingInvoice({ tenantId: 't1', invoiceId: 'in_123' })).rejects.toThrow(
      'Billing is disabled.',
    );
    fetchSpy.mockRestore();
  });
});
