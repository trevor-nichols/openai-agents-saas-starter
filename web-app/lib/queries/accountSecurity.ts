import { useMutation } from '@tanstack/react-query';

import { changePasswordRequest } from '@/lib/api/accountSecurity';
import type { PasswordChangeRequest } from '@/lib/api/client/types.gen';

export function useChangePasswordMutation() {
  return useMutation({
    mutationFn: (payload: PasswordChangeRequest) => changePasswordRequest(payload),
  });
}
