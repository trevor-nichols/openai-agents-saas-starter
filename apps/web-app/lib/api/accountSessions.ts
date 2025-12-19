import type {
  LogoutAllSessionsSuccessResponse,
  SessionRevokeByIdSuccessResponse,
  UserSessionListResponse,
} from '@/lib/api/client/types.gen';
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
  const payload = await parseJson<
    { success?: boolean; error?: string; message?: string } & Partial<SessionListPayload>
  >(response);

  if (!response.ok || payload.success === false || !payload.sessions) {
    throw new Error(payload.message || payload.error || 'Unable to load sessions.');
  }

  const result: SessionListPayload = {
    sessions: payload.sessions,
    total: payload.total ?? payload.sessions.length,
    limit: payload.limit ?? params.limit ?? payload.sessions.length,
    offset: payload.offset ?? params.offset ?? 0,
  };
  return result;
}

export async function revokeSessionRequest(sessionId: string): Promise<SessionRevokeByIdSuccessResponse> {
  if (!sessionId) {
    throw new Error('Session id is required.');
  }
  const response = await fetch(apiV1Path(`/auth/sessions/${sessionId}`), {
    method: 'DELETE',
    cache: 'no-store',
  });
  const payload = await parseJson<SessionRevokeByIdSuccessResponse | { message?: string }>(response);
  if (!response.ok) {
    throw new Error('message' in payload && payload.message ? payload.message : 'Failed to revoke session.');
  }
  return payload as SessionRevokeByIdSuccessResponse;
}

export async function logoutAllSessionsRequest(): Promise<LogoutAllSessionsSuccessResponse> {
  const response = await fetch(apiV1Path('/auth/logout/all'), {
    method: 'POST',
    cache: 'no-store',
  });
  const payload = await parseJson<
    LogoutAllSessionsSuccessResponse | { success?: boolean; error?: string; message?: string }
  >(response);
  if (!response.ok || payload.success === false || !('message' in payload)) {
    throw new Error(
      ('message' in payload && payload.message) || ('error' in payload && payload.error)
        ? String(('message' in payload && payload.message) || ('error' in payload && payload.error))
        : 'Failed to sign out of all sessions.',
    );
  }
  return payload as LogoutAllSessionsSuccessResponse;
}
