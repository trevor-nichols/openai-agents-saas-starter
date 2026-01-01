'use server';

import { cookies } from 'next/headers';

import { SSO_REDIRECT_COOKIE } from '@/lib/config';
import { SECURE_COOKIE_BASE } from './cookieConfig';

const SSO_REDIRECT_TTL_SECONDS = 15 * 60;

export async function setSsoRedirectCookie(target: string): Promise<void> {
  const store = await cookies();
  store.set({
    ...SECURE_COOKIE_BASE,
    name: SSO_REDIRECT_COOKIE,
    value: target,
    maxAge: SSO_REDIRECT_TTL_SECONDS,
  });
}

export async function readSsoRedirectCookie(): Promise<string | null> {
  const store = await cookies();
  return store.get(SSO_REDIRECT_COOKIE)?.value ?? null;
}

export async function clearSsoRedirectCookie(): Promise<void> {
  const store = await cookies();
  store.set({
    ...SECURE_COOKIE_BASE,
    name: SSO_REDIRECT_COOKIE,
    value: '',
    expires: new Date(0),
  });
}
