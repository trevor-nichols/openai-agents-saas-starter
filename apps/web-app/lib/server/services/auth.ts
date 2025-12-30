'use server';

import {
  getCurrentUserInfoApiV1AuthMeGet,
  loginForAccessTokenApiV1AuthTokenPost,
  refreshAccessTokenApiV1AuthRefreshPost,
} from '@/lib/api/client/sdk.gen';
import type {
  CurrentUserInfoSuccessResponse,
  MfaChallengeResponse,
  UserLoginRequest,
  UserRefreshRequest,
  UserSessionResponse,
} from '@/lib/api/client/types.gen';
import type { UserSessionTokens } from '@/lib/types/auth';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { USE_API_MOCK } from '@/lib/config';
import { createApiClient, getServerApiClient } from '../apiClient';
import { MfaRequiredError } from './auth.errors';

export type CurrentUserProfile = Record<string, unknown>;

/**
 * Exchange credentials for a session token pair using the backend auth API.
 */
export async function loginWithCredentials(
  payload: UserLoginRequest,
): Promise<UserSessionTokens> {
  const response = await loginForAccessTokenApiV1AuthTokenPost({
    client: createApiClient(),
    body: payload,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.data) {
    throw new Error('Auth service returned an empty response.');
  }

  if ('mfa_required' in response.data) {
    throw new MfaRequiredError(response.data as MfaChallengeResponse);
  }

  return mapSessionResponse(response.data as UserSessionResponse);
}

/**
 * Exchange a refresh token for a new session token pair.
 */
export async function refreshSessionTokens(
  payload: UserRefreshRequest,
): Promise<UserSessionTokens> {
  const response = await refreshAccessTokenApiV1AuthRefreshPost({
    client: createApiClient(),
    body: payload,
    responseStyle: 'fields',
    throwOnError: true,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.data) {
    throw new Error('Refresh endpoint returned an empty response.');
  }

  return mapSessionResponse(response.data);
}

/**
 * Fetch profile metadata for the currently authenticated user.
 */
export async function getCurrentUserProfile<TProfile extends CurrentUserProfile = CurrentUserProfile>(): Promise<TProfile> {
  if (USE_API_MOCK) {
    const meta = await getSessionMetaFromCookies();
    const profile: CurrentUserProfile = {
      user_id: meta?.userId ?? '99999999-8888-7777-6666-555555555555',
      token_payload: {
        scopes: meta?.scopes ?? ['conversations:read', 'conversations:write'],
        tenant_id: meta?.tenantId ?? '11111111-2222-3333-4444-555555555555',
      },
    };
    return profile as unknown as TProfile;
  }

  const { client, auth } = await getServerApiClient();
  const response = await getCurrentUserInfoApiV1AuthMeGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: true,
  });

  const payload = response.data as CurrentUserInfoSuccessResponse | undefined;
  const data = (payload?.data ?? null) as TProfile | null;

  if (payload?.success === false || !data) {
    throw new Error(payload?.message ?? 'Unable to load current user profile.');
  }

  return data;
}

function mapSessionResponse(payload: UserSessionResponse): UserSessionTokens {
  return {
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
}
