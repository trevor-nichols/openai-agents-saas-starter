import { describe, expect, it, vi } from 'vitest';

import { fetchBillingUsageTotals } from '../billingUsageTotals';

describe('fetchBillingUsageTotals', () => {
  it('returns empty list when billing is disabled', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    const result = await fetchBillingUsageTotals({ tenantId: 'tenant-1' });

    expect(result).toEqual([]);
    fetchSpy.mockRestore();
  });

  it('throws on non-ok responses', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Tenant not found.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    await expect(fetchBillingUsageTotals({ tenantId: 'tenant-1' })).rejects.toThrow('Tenant not found.');
    fetchSpy.mockRestore();
  });
});
