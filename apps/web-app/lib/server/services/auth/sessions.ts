import 'server-only';

import {
  listUserSessionsApiV1AuthSessionsGet,
  logoutAllSessionsApiV1AuthLogoutAllPost,
  logoutSessionApiV1AuthLogoutPost,
  revokeUserSessionApiV1AuthSessionsSessionIdDelete,
} from '@/lib/api/client/sdk.gen';
import type {
  LogoutAllSessionsSuccessResponse,
  SessionRevokeByIdSuccessResponse,
  UserLogoutRequest,
  UserSessionListResponse,
} from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../../apiClient';

export interface SessionListParams {
  includeRevoked?: boolean;
  limit?: number;
  offset?: number;
  tenantId?: string | null;
}

export async function listUserSessions(params: SessionListParams = {}): Promise<UserSessionListResponse> {
  const { client, auth } = await getServerApiClient();

  const response = await listUserSessionsApiV1AuthSessionsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    query: {
      include_revoked: params.includeRevoked ?? false,
      limit: params.limit,
      offset: params.offset,
      tenant_id: params.tenantId ?? undefined,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Failed to load sessions.');
  }

  return payload;
}

export async function logoutSession(payload: UserLogoutRequest): Promise<void> {
  const { client, auth } = await getServerApiClient();
  await logoutSessionApiV1AuthLogoutPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    body: payload,
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

export async function logoutAllSessions(): Promise<LogoutAllSessionsSuccessResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await logoutAllSessionsApiV1AuthLogoutAllPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Logout-all endpoint returned no data.');
  }

  return payload;
}

export async function revokeUserSession(sessionId: string): Promise<SessionRevokeByIdSuccessResponse> {
  if (!sessionId) {
    throw new Error('Session id is required.');
  }
  const { client, auth } = await getServerApiClient();
  const response = await revokeUserSessionApiV1AuthSessionsSessionIdDelete({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
    path: {
      session_id: sessionId,
    },
  });

  const payload = response.data;
  if (!payload) {
    throw new Error('Failed to revoke session.');
  }

  return payload;
}
