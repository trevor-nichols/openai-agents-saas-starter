'use server';

import { cookies } from 'next/headers';

import { ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, SESSION_META_COOKIE } from '../config';
import type { UserSessionTokens } from '../types/auth';
import { META_COOKIE_BASE, SECURE_COOKIE_BASE } from './cookieConfig';

export async function persistSessionCookies(tokens: UserSessionTokens): Promise<void> {
  const store = await cookies();

  store.set({
    ...SECURE_COOKIE_BASE,
    name: ACCESS_TOKEN_COOKIE,
    value: tokens.access_token,
    expires: new Date(tokens.expires_at),
  });

  store.set({
    ...SECURE_COOKIE_BASE,
    name: REFRESH_TOKEN_COOKIE,
    value: tokens.refresh_token,
    expires: new Date(tokens.refresh_expires_at),
    sameSite: 'strict',
  });

  const metaPayload = {
    expiresAt: tokens.expires_at,
    refreshExpiresAt: tokens.refresh_expires_at,
    userId: tokens.user_id,
    tenantId: tokens.tenant_id,
    scopes: tokens.scopes,
  };

  store.set({
    ...META_COOKIE_BASE,
    name: SESSION_META_COOKIE,
    value: Buffer.from(JSON.stringify(metaPayload)).toString('base64url'),
    expires: new Date(tokens.refresh_expires_at),
  });
}

export async function clearSessionCookies(): Promise<void> {
  const store = await cookies();
  const names = [ACCESS_TOKEN_COOKIE, REFRESH_TOKEN_COOKIE, SESSION_META_COOKIE];
  names.forEach((name) => {
    const base =
      name === SESSION_META_COOKIE
        ? META_COOKIE_BASE
        : SECURE_COOKIE_BASE;
    store.set({
      name,
      value: '',
      ...base,
      expires: new Date(0),
    });
  });
}

export async function getAccessTokenFromCookies(): Promise<string | null> {
  const token = (await cookies()).get(ACCESS_TOKEN_COOKIE);
  return token?.value ?? null;
}

export async function getRefreshTokenFromCookies(): Promise<string | null> {
  const token = (await cookies()).get(REFRESH_TOKEN_COOKIE);
  return token?.value ?? null;
}

export async function getSessionMetaFromCookies(): Promise<{
  expiresAt: string;
  refreshExpiresAt: string;
  userId: string;
  tenantId: string;
  scopes: string[];
} | null> {
  const raw = (await cookies()).get(SESSION_META_COOKIE)?.value;
  if (!raw) return null;
  try {
    const decoded = Buffer.from(raw, 'base64url').toString('utf-8');
    return JSON.parse(decoded);
  } catch (error) {
    console.warn('[auth] Failed to parse session meta cookie', error);
    return null;
  }
}
