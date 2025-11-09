'use server';

import { API_BASE_URL, USE_API_MOCK } from '../config';
import type { SessionSummary, UserSessionTokens } from '../types/auth';
import {
  clearSessionCookies,
  getAccessTokenFromCookies,
  getSessionMetaFromCookies,
  persistSessionCookies,
} from './cookies';

export async function exchangeCredentials(
  payload: Record<string, unknown>,
): Promise<UserSessionTokens> {
  if (USE_API_MOCK) {
    const tokens = createMockTokens();
    persistSessionCookies(tokens);
    return tokens;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  const tokens = (await response.json()) as UserSessionTokens;
  persistSessionCookies(tokens);
  return tokens;
}

export async function refreshSessionWithBackend(refreshToken: string): Promise<UserSessionTokens> {
  if (USE_API_MOCK) {
    const tokens = createMockTokens();
    persistSessionCookies(tokens);
    return tokens;
  }
  const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: 'no-store',
  });
  if (!response.ok) {
    throw new Error(await response.text());
  }
  const tokens = (await response.json()) as UserSessionTokens;
  persistSessionCookies(tokens);
  return tokens;
}

export async function loadSessionSummary(): Promise<SessionSummary | null> {
  const accessToken = getAccessTokenFromCookies();
  if (!accessToken) {
    return null;
  }
  const meta = getSessionMetaFromCookies();
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

export function destroySession(): void {
  clearSessionCookies();
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
