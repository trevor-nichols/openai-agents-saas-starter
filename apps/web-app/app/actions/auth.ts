'use server';

import { redirect } from 'next/navigation';

import { getRefreshTokenFromCookies } from '@/lib/auth/cookies';
import { destroySession, exchangeCredentials, refreshSessionWithBackend } from '@/lib/auth/session';

interface LoginActionInput {
  email: string;
  password: string;
  tenantId?: string | null;
}

interface AuthActionResult {
  success: boolean;
  error?: string;
}

export async function loginAction({ email, password, tenantId }: LoginActionInput): Promise<AuthActionResult> {
  if (!email || !password) {
    return { success: false, error: 'Email and password are required.' };
  }

  const tenantIdValue = tenantId && tenantId.trim().length > 0 ? tenantId.trim() : null;

  try {
    await exchangeCredentials({
      email,
      password,
      tenant_id: tenantIdValue,
    });
    return { success: true };
  } catch (error) {
    return { success: false, error: resolveAuthErrorMessage(error) };
  }
}

export async function logoutAction(): Promise<void> {
  destroySession();
  redirect('/login');
}

export async function silentRefreshAction(): Promise<void> {
  const refreshToken = await getRefreshTokenFromCookies();
  if (!refreshToken) {
    await destroySession();
    redirect('/login');
  }
  await refreshSessionWithBackend(refreshToken);
}

function resolveAuthErrorMessage(error: unknown): string {
  if (error instanceof Error && error.message) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  if (error && typeof error === 'object') {
    const maybeMessage = (error as { message?: unknown }).message;
    if (typeof maybeMessage === 'string' && maybeMessage.trim()) {
      return maybeMessage;
    }
    const maybeDetail = (error as { detail?: unknown }).detail;
    if (typeof maybeDetail === 'string' && maybeDetail.trim()) {
      return maybeDetail;
    }
  }

  return 'Invalid email or password. Please try again.';
}
