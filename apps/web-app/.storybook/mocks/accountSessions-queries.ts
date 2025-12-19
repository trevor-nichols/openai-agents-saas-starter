import { mockSessions } from './account-fixtures';

export function useUserSessionsQuery() {
  return {
    data: { sessions: mockSessions, total: mockSessions.length, limit: 50, offset: 0 },
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: async () => {},
  };
}

export function useRevokeSessionMutation() {
  return {
    isPending: false,
    mutateAsync: async (_sessionId: string) => {
      return { revoked: 1 };
    },
  };
}

export function useLogoutAllSessionsMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { data: { revoked: mockSessions.length } };
    },
  };
}
