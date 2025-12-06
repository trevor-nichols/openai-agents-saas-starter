'use server';

import { redirect } from 'next/navigation';

import {
  adminResetPassword,
  changePassword,
  confirmPasswordReset,
  requestPasswordReset,
} from '@/lib/server/services/auth/passwords';
import type {
  PasswordChangeRequest,
  PasswordForgotRequest,
  PasswordResetConfirmRequest,
  PasswordResetRequest,
} from '@/lib/api/client/types.gen';

export async function requestPasswordResetAction(
  payload: PasswordForgotRequest,
  options?: { redirectTo?: string },
) {
  const result = await requestPasswordReset(payload);
  if (options?.redirectTo) {
    redirect(options.redirectTo);
  }
  return result;
}

export async function confirmPasswordResetAction(
  payload: PasswordResetConfirmRequest,
  options?: { redirectTo?: string },
) {
  const result = await confirmPasswordReset(payload);
  if (options?.redirectTo) {
    redirect(options.redirectTo);
  }
  return result;
}

export async function changePasswordAction(
  payload: PasswordChangeRequest,
  options?: { redirectTo?: string },
) {
  const result = await changePassword(payload);
  if (options?.redirectTo) {
    redirect(options.redirectTo);
  }
  return result;
}

export async function adminResetPasswordAction(payload: PasswordResetRequest) {
  return adminResetPassword(payload);
}

