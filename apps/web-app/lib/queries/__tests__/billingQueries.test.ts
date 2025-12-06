import type { UseQueryOptions } from '@tanstack/react-query';
import { afterEach, describe, expect, it, vi } from 'vitest';

type UseQueryOptionsParam = UseQueryOptions<unknown, unknown, unknown, readonly unknown[]>;
type UseQueryFn = (options: UseQueryOptionsParam) => unknown;
const mockedUseQuery = vi.fn<UseQueryFn>();

vi.mock('@tanstack/react-query', () => ({
  useQuery: mockedUseQuery,
}));

const fetchBillingPlans = vi.fn();
vi.mock('@/lib/api/billingPlans', () => ({
  fetchBillingPlans: (...args: unknown[]) => fetchBillingPlans(...args),
}));

describe('billing query guards', () => {
  afterEach(() => {
    vi.resetModules();
    mockedUseQuery.mockReset();
    fetchBillingPlans.mockReset();
    delete process.env.NEXT_PUBLIC_ENABLE_BILLING;
  });

  it('disables billing plans query when billing is off', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'false';
    vi.doMock('@/lib/config/features', () => ({ billingEnabled: false }));
    const { useBillingPlans } = await import('../billingPlans');

    mockedUseQuery.mockReturnValue({});
    useBillingPlans();

    const call = mockedUseQuery.mock.calls[0]?.[0];
    expect(call).toBeDefined();
    if (!call) throw new Error('useQuery was not called');
    expect(call.enabled).toBe(false);
    expect(fetchBillingPlans).not.toHaveBeenCalled();
  });

  it('enables billing plans query when billing is on', async () => {
    process.env.NEXT_PUBLIC_ENABLE_BILLING = 'true';
    vi.doMock('@/lib/config/features', () => ({ billingEnabled: true }));
    const { useBillingPlans } = await import('../billingPlans');

    mockedUseQuery.mockReturnValue({});
    useBillingPlans();

    const call = mockedUseQuery.mock.calls[0]?.[0];
    expect(call).toBeDefined();
    if (!call) throw new Error('useQuery was not called');
    expect(call.enabled).toBe(true);
    expect(call.queryFn).toBeDefined();
  });
});
