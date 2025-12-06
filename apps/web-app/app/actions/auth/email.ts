'use server';

import { redirect } from 'next/navigation';

import { sendVerificationEmail, verifyEmailToken } from '@/lib/server/services/auth/email';
import type { EmailVerificationConfirmRequest } from '@/lib/api/client/types.gen';

export async function sendVerificationEmailAction() {
  return sendVerificationEmail();
}

export async function verifyEmailTokenAction(
  payload: EmailVerificationConfirmRequest,
  options?: { redirectTo?: string },
) {
  const result = await verifyEmailToken(payload);
  if (options?.redirectTo) {
    redirect(options.redirectTo);
  }
  return result;
}

