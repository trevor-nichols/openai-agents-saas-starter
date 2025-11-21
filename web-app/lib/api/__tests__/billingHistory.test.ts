import { describe, expect, it, vi } from 'vitest';

import { fetchBillingHistory } from '../billingHistory';

describe('fetchBillingHistory', () => {
  it('returns empty when billing is disabled (404 + message)', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    const result = await fetchBillingHistory({ tenantId: 't1' });

    expect(result).toEqual({ items: [], next_cursor: null });
    fetchSpy.mockRestore();
  });

  it('throws on other 404s (e.g., tenant not found)', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Tenant not found.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(fetchBillingHistory({ tenantId: 'missing' })).rejects.toThrow('Tenant not found.');
    fetchSpy.mockRestore();
  });
});
