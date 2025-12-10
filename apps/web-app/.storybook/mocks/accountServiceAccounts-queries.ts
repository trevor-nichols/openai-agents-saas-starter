import { mockIssueResult, mockServiceAccountTokens } from './account-fixtures';

export function useServiceAccountTokensQuery() {
  return {
    data: {
      tokens: mockServiceAccountTokens,
      total: mockServiceAccountTokens.length,
      limit: mockServiceAccountTokens.length,
      offset: 0,
    },
    isLoading: false,
    isFetching: false,
    error: null,
    refetch: async () => {},
  };
}

export function useRevokeServiceAccountTokenMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { success: true };
    },
  };
}

export function useIssueServiceAccountTokenMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return mockIssueResult;
    },
  };
}
