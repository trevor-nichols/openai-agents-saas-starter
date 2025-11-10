'use server';

import { redirect } from 'next/navigation';

import { getRefreshTokenFromCookies } from '@/lib/auth/cookies';
import { destroySession, exchangeCredentials, refreshSessionWithBackend } from '@/lib/auth/session';

interface ActionState {
  error?: string;
}

export async function loginAction(_prev: ActionState, formData: FormData): Promise<ActionState> {
  const email = formData.get('email');
  const password = formData.get('password');
  const tenantId = formData.get('tenantId');
  const redirectToRaw = (formData.get('redirectTo') as string) || '/';
  const redirectTo = redirectToRaw.startsWith('/') ? redirectToRaw : '/';

  if (!email || !password || typeof email !== 'string' || typeof password !== 'string') {
    return { error: 'Email and password are required.' };
  }

  const tenantIdValue =
    typeof tenantId === 'string' && tenantId.trim().length > 0 ? tenantId : null;

  try {
    await exchangeCredentials({
      email,
      password,
      tenant_id: tenantIdValue,
    });
  } catch (error) {
    return { error: error instanceof Error ? error.message : 'Login failed.' };
  }

  redirect(redirectTo);
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
