'use server';

import { redirect } from 'next/navigation';

import { getRefreshTokenFromCookies } from '@/lib/auth/cookies';
import { destroySession, exchangeCredentials, refreshSessionWithBackend } from '@/lib/auth/session';

interface LoginActionInput {
  email: string;
  password: string;
  tenantId?: string | null;
}

export async function loginAction({ email, password, tenantId }: LoginActionInput): Promise<void> {
  if (!email || !password) {
    throw new Error('Email and password are required.');
  }

  const tenantIdValue = tenantId && tenantId.trim().length > 0 ? tenantId.trim() : null;

  try {
    await exchangeCredentials({
      email,
      password,
      tenant_id: tenantIdValue,
    });
  } catch (error) {
    throw new Error(error instanceof Error ? error.message : 'Login failed.');
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
