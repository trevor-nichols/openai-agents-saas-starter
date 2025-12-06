import { useMutation } from '@tanstack/react-query';

import { adminResetPasswordRequest, changePasswordRequest } from '@/lib/api/accountSecurity';
import type { PasswordChangeRequest, PasswordResetRequest } from '@/lib/api/client/types.gen';

export function useChangePasswordMutation() {
  return useMutation({
    mutationFn: (payload: PasswordChangeRequest) => changePasswordRequest(payload),
  });
}

export function useAdminResetPasswordMutation() {
  return useMutation({
    mutationFn: (payload: PasswordResetRequest) => adminResetPasswordRequest(payload),
  });
}
