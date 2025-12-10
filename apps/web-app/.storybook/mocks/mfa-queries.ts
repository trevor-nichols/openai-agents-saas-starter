const mockMethods = [
  {
    id: 'mfa-1',
    method_type: 'totp',
    label: 'Authenticator App',
    verified_at: new Date().toISOString(),
    last_used_at: new Date(Date.now() - 60 * 60 * 1000).toISOString(),
    revoked_at: null,
  },
];

export function useMfaMethodsQuery() {
  return {
    data: mockMethods,
    isLoading: false,
    refetch: async () => {},
  };
}

export function useRevokeMfaMethodMutation() {
  return {
    isPending: false,
    mutateAsync: async () => ({ success: true }),
  };
}

export function useRegenerateRecoveryCodesMutation() {
  return {
    isPending: false,
    mutateAsync: async () => ({
      codes: ['123456', '234567', '345678', '456789', '567890'],
    }),
  };
}

export function useStartTotpEnrollmentMutation() {
  return {
    isPending: false,
    mutateAsync: async () => ({
      secret: 'MOCKSECRET',
      method_id: 'mfa-new',
      otpauth_url: 'otpauth://totp/mock',
    }),
  };
}

export function useVerifyTotpMutation() {
  return {
    isPending: false,
    mutateAsync: async () => ({ success: true }),
  };
}

export const useCompleteMfaChallengeMutation = () => ({
  mutateAsync: async () => ({ success: true }),
  isPending: false,
});
