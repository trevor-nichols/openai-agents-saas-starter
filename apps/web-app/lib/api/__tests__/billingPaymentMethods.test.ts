import { describe, expect, it, vi } from 'vitest';

import {
  fetchPaymentMethods,
  setDefaultPaymentMethodRequest,
} from '../billingPaymentMethods';

describe('billingPaymentMethods helpers', () => {
  it('returns payment methods on success', async () => {
    const mockResponse = new Response(
      JSON.stringify([{ id: 'pm_1', brand: 'visa', last4: '4242', is_default: true }]),
      { status: 200, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    const methods = await fetchPaymentMethods('tenant-1');

    expect(methods).toHaveLength(1);
    expect(methods[0]?.id).toBe('pm_1');
    fetchSpy.mockRestore();
  });

  it('throws billing disabled on 404 payload', async () => {
    const mockResponse = new Response(JSON.stringify({ message: 'Billing is disabled.' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    await expect(fetchPaymentMethods('tenant-1')).rejects.toThrow('Billing is disabled.');
    fetchSpy.mockRestore();
  });

  it('surfaces default payment method errors', async () => {
    const mockResponse = new Response(JSON.stringify({ message: 'Forbidden' }), {
      status: 403,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    await expect(setDefaultPaymentMethodRequest('tenant-1', 'pm_1')).rejects.toThrow('Forbidden');
    fetchSpy.mockRestore();
  });
});
