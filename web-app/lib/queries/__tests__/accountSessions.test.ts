import { describe, expect, it, vi, afterEach } from 'vitest';

import type { UseQueryOptions } from '@tanstack/react-query';

import { useUserSessionsQuery } from '@/lib/queries/accountSessions';
import { queryKeys } from '@/lib/queries/keys';

type UseQueryOptionsParam = UseQueryOptions<unknown, unknown, unknown, readonly unknown[]>;
type UseQueryFn = (options?: UseQueryOptionsParam) => unknown;
const mockedUseQuery = vi.hoisted(() => vi.fn<UseQueryFn>());

vi.mock('@tanstack/react-query', () => ({
  useQuery: mockedUseQuery,
}));

const fetchUserSessions = vi.hoisted(() => vi.fn());
vi.mock('@/lib/api/accountSessions', () => ({
  fetchUserSessions: (...args: unknown[]) => fetchUserSessions(...args),
}));

describe('useUserSessionsQuery', () => {
  afterEach(() => {
    mockedUseQuery.mockReset();
    fetchUserSessions.mockReset();
  });

  it('includes tenantId in query key and fetch params when provided', () => {
    mockedUseQuery.mockImplementation((options) => {
      options?.queryFn?.();
      return {};
    });

    useUserSessionsQuery({ limit: 10, offset: 5, includeRevoked: true, tenantId: 'tenant-123' });

    expect(mockedUseQuery).toHaveBeenCalledWith({
      queryKey: queryKeys.account.sessions.list({
        limit: 10,
        offset: 5,
        tenantId: 'tenant-123',
        includeRevoked: true,
      }),
      queryFn: expect.any(Function),
      staleTime: 15 * 1000,
    });

    expect(fetchUserSessions).toHaveBeenCalledWith({
      limit: 10,
      offset: 5,
      includeRevoked: true,
      tenantId: 'tenant-123',
    });
  });

  it('defaults to all tenants when no filter is supplied', () => {
    mockedUseQuery.mockImplementation((options) => {
      options?.queryFn?.();
      return {};
    });

    useUserSessionsQuery();

    expect(fetchUserSessions).toHaveBeenCalledWith({
      limit: 20,
      offset: 0,
      includeRevoked: false,
      tenantId: null,
    });
  });
});
