import { mockConsents } from './account-fixtures';

export function useConsentsQuery() {
  return {
    data: mockConsents,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}

export function useRecordConsentMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { success: true };
    },
  };
}
