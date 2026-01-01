'use server';

import type { UserLoginRequest, UserRefreshRequest, UserSessionResponse } from '@/lib/api/client/types.gen';
import { loginWithCredentials, refreshSessionTokens } from '@/lib/server/services/auth';
import { USE_API_MOCK } from '../config';
import type { SessionSummary, UserSessionTokens } from '../types/auth';
import {
  clearSessionCookies,
  getAccessTokenFromCookies,
  getSessionMetaFromCookies,
  persistSessionCookies,
} from './cookies';

export async function exchangeCredentials(
  payload: UserLoginRequest,
): Promise<UserSessionTokens> {
  if (USE_API_MOCK) {
    const tokens = createMockTokens();
    await persistSessionCookies(tokens);
    return tokens;
  }
  const tokens = await loginWithCredentials(payload);
  await persistSessionCookies(tokens);
  return tokens;
}

export async function persistSessionFromResponse(payload: UserSessionResponse): Promise<UserSessionTokens> {
  const tokens: UserSessionTokens = {
    access_token: payload.access_token,
    refresh_token: payload.refresh_token,
    token_type: payload.token_type ?? 'bearer',
    expires_at: payload.expires_at,
    refresh_expires_at: payload.refresh_expires_at,
    kid: payload.kid,
    refresh_kid: payload.refresh_kid,
    scopes: payload.scopes,
    tenant_id: payload.tenant_id,
    user_id: payload.user_id,
  };
  await persistSessionCookies(tokens);
  return tokens;
}

export async function refreshSessionWithBackend(refreshToken: string): Promise<UserSessionTokens> {
  if (USE_API_MOCK) {
    const tokens = createMockTokens();
    await persistSessionCookies(tokens);
    return tokens;
  }
  const payload: UserRefreshRequest = {
    refresh_token: refreshToken,
  };
  const tokens = await refreshSessionTokens(payload);
  await persistSessionCookies(tokens);
  return tokens;
}

export async function loadSessionSummary(): Promise<SessionSummary | null> {
  const accessToken = await getAccessTokenFromCookies();
  if (!accessToken) {
    return null;
  }
  const meta = await getSessionMetaFromCookies();
  if (!meta) {
    return null;
  }
  return {
    userId: meta.userId,
    tenantId: meta.tenantId,
    scopes: meta.scopes,
    expiresAt: meta.expiresAt,
  };
}

export async function destroySession(): Promise<void> {
  await clearSessionCookies();
}

function createMockTokens(): UserSessionTokens {
  const now = Date.now();
  return {
    access_token: `mock-access-${now}`,
    refresh_token: `mock-refresh-${now}`,
    token_type: 'bearer',
    expires_at: new Date(now + 15 * 60 * 1000).toISOString(),
    refresh_expires_at: new Date(now + 7 * 24 * 60 * 60 * 1000).toISOString(),
    kid: 'mock-kid',
    refresh_kid: 'mock-refresh-kid',
    scopes: ['conversations:read', 'conversations:write'],
    tenant_id: '11111111-2222-3333-4444-555555555555',
    user_id: '99999999-8888-7777-6666-555555555555',
  };
}
