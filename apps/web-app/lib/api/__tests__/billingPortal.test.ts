import { describe, expect, it, vi } from 'vitest';

import { createBillingPortalSession } from '../billingPortal';

describe('billingPortal helpers', () => {
  it('throws billing disabled on 404 payload', async () => {
    const mockResponse = new Response(JSON.stringify({ message: 'Billing is disabled.' }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    await expect(
      createBillingPortalSession('tenant-1', { billing_email: 'billing@example.com' }),
    ).rejects.toThrow('Billing is disabled.');
    fetchSpy.mockRestore();
  });

  it('returns portal session on success', async () => {
    const mockResponse = new Response(JSON.stringify({ url: 'https://stripe.example/portal' }), {
      status: 200,
      headers: { 'Content-Type': 'application/json' },
    });
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as Response);

    const payload = await createBillingPortalSession('tenant-1', { billing_email: 'billing@example.com' });

    expect(payload.url).toBe('https://stripe.example/portal');
    fetchSpy.mockRestore();
  });
});
