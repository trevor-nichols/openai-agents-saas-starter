import { describe, expect, it, vi, afterEach, type MockedFunction } from 'vitest';

import { useQuery } from '@tanstack/react-query';

import { useUserSessionsQuery } from '@/lib/queries/accountSessions';
import { queryKeys } from '@/lib/queries/keys';

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(),
}));

const fetchUserSessions = vi.fn();
vi.mock('@/lib/api/accountSessions', () => ({
  fetchUserSessions: (...args: unknown[]) => fetchUserSessions(...args),
}));

type UseQueryOptionsParam = Parameters<typeof useQuery>[0];
const mockedUseQuery = useQuery as unknown as MockedFunction<typeof useQuery>;

describe('useUserSessionsQuery', () => {
  afterEach(() => {
    mockedUseQuery.mockReset();
    fetchUserSessions.mockReset();
  });

  it('includes tenantId in query key and fetch params when provided', () => {
    mockedUseQuery.mockImplementation((options: UseQueryOptionsParam) => {
      if (options?.queryFn) {
        void options.queryFn();
      }
      return {} as unknown as ReturnType<typeof useQuery>;
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
    mockedUseQuery.mockImplementation((options: UseQueryOptionsParam) => {
      if (options?.queryFn) {
        void options.queryFn();
      }
      return {} as unknown as ReturnType<typeof useQuery>;
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
