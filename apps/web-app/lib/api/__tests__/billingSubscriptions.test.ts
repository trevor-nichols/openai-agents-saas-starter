import { describe, expect, it, vi } from 'vitest';

import { changeSubscriptionPlanRequest, fetchTenantSubscription, recordUsageRequest } from '../billingSubscriptions';

describe('billingSubscriptions helpers', () => {
  it('throws explicit billing disabled message on 404 with disabled payload', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(fetchTenantSubscription('t1')).rejects.toThrow('Billing is disabled.');
    fetchSpy.mockRestore();
  });

  it('surfaces subscription not found errors (404) without relabeling as disabled', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Subscription not found.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(fetchTenantSubscription('missing-tenant')).rejects.toThrow('Subscription not found.');
    fetchSpy.mockRestore();
  });

  it('passes through backend usage errors', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Quota exceeded.' }),
      { status: 429, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(
      recordUsageRequest('tenant-1', { quantity: 10, feature_key: 'messages' }, {}),
    ).rejects.toThrow('Quota exceeded.');
    fetchSpy.mockRestore();
  });

  it('throws billing disabled specifically for usage 404 payload', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Billing is disabled.' }),
      { status: 404, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(
      recordUsageRequest('tenant-1', { quantity: 1, feature_key: 'messages' }, {}),
    ).rejects.toThrow('Billing is disabled.');
    fetchSpy.mockRestore();
  });

  it('surfaces plan change errors', async () => {
    const mockResponse = new Response(
      JSON.stringify({ message: 'Plan change not allowed.' }),
      { status: 409, headers: { 'Content-Type': 'application/json' } },
    );
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse as unknown as Response);

    await expect(
      changeSubscriptionPlanRequest('tenant-1', { plan_code: 'pro', timing: 'immediate' }),
    ).rejects.toThrow('Plan change not allowed.');
    fetchSpy.mockRestore();
  });
});
