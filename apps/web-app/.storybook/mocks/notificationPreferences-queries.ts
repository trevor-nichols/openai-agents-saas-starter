import { mockNotificationPreferences } from './account-fixtures';

export function useNotificationPreferencesQuery() {
  return {
    data: mockNotificationPreferences,
    isLoading: false,
    error: null,
    refetch: async () => {},
  };
}

export function useUpsertNotificationPreferenceMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { success: true };
    },
  };
}
