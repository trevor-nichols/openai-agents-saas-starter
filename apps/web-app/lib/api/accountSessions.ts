import type { SuccessResponse, UserSessionListResponse } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

export interface SessionListParams {
  limit?: number;
  offset?: number;
  includeRevoked?: boolean;
  tenantId?: string | null;
}

export type SessionListPayload = UserSessionListResponse;

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse session response.');
  }
}

export async function fetchUserSessions(params: SessionListParams = {}): Promise<SessionListPayload> {
  const search = new URLSearchParams();
  if (typeof params.limit === 'number') {
    search.set('limit', String(params.limit));
  }
  if (typeof params.offset === 'number') {
    search.set('offset', String(params.offset));
  }
  if (typeof params.includeRevoked === 'boolean') {
    search.set('include_revoked', String(params.includeRevoked));
  }
  if (params.tenantId) {
    search.set('tenant_id', params.tenantId);
  }

  const response = await fetch(apiV1Path(`/auth/sessions?${search.toString()}`), { cache: 'no-store' });
  const payload = await parseJson<{ success?: boolean; error?: string } & Partial<SessionListPayload>>(response);

  if (!response.ok || payload.success === false || !payload.sessions) {
    throw new Error(payload.error || 'Unable to load sessions.');
  }

  const result: SessionListPayload = {
    sessions: payload.sessions,
    total: payload.total ?? payload.sessions.length,
    limit: payload.limit ?? params.limit ?? payload.sessions.length,
    offset: payload.offset ?? params.offset ?? 0,
  };
  return result;
}

export async function revokeSessionRequest(sessionId: string): Promise<SuccessResponse> {
  if (!sessionId) {
    throw new Error('Session id is required.');
  }
  const response = await fetch(apiV1Path(`/auth/sessions/${sessionId}`), {
    method: 'DELETE',
    cache: 'no-store',
  });
  const payload = await parseJson<SuccessResponse | { message?: string }>(response);
  if (!response.ok) {
    throw new Error('message' in payload && payload.message ? payload.message : 'Failed to revoke session.');
  }
  return payload as SuccessResponse;
}

export interface LogoutAllResponse {
  success: boolean;
  data?: { revoked?: number };
  message?: string;
  error?: string;
}

export async function logoutAllSessionsRequest(): Promise<LogoutAllResponse> {
  const response = await fetch(apiV1Path('/auth/logout/all'), {
    method: 'POST',
    cache: 'no-store',
  });
  const payload = await parseJson<LogoutAllResponse>(response);
  if (!response.ok || payload.success === false) {
    throw new Error(payload.error || 'Failed to sign out of all sessions.');
  }
  return payload;
}
