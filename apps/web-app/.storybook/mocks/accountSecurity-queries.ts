export function useChangePasswordMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { success: true };
    },
  };
}

export function useAdminResetPasswordMutation() {
  return {
    isPending: false,
    mutateAsync: async () => {
      return { success: true };
    },
  };
}
