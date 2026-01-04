'use server';

import {
  changeCurrentUserEmailApiV1UsersMeEmailPatch,
  disableCurrentUserAccountApiV1UsersMeDisablePost,
  getCurrentUserProfileApiV1UsersMeGet,
  listConsentsApiV1UsersConsentsGet,
  listNotificationPreferencesApiV1UsersNotificationPreferencesGet,
  recordConsentApiV1UsersConsentsPost,
  updateCurrentUserProfileApiV1UsersMeProfilePatch,
  upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut,
} from '@/lib/api/client/sdk.gen';
import type {
  ConsentRequest,
  ConsentView,
  CurrentUserProfileResponseData,
  CurrentUserProfileSuccessResponse,
  NotificationPreferenceRequest,
  NotificationPreferenceView,
  SuccessNoDataResponse,
  UserAccountDisableRequest,
  UserAccountDisableResponseData,
  UserAccountDisableSuccessResponse,
  UserEmailChangeRequest,
  UserEmailChangeResponseData,
  UserEmailChangeSuccessResponse,
  UserProfileUpdateRequest,
} from '@/lib/api/client/types.gen';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { USE_API_MOCK } from '@/lib/config';
import { getServerApiClient } from '../apiClient';
import { UserProfileApiError } from './users.errors';

type SdkFieldsResult<T> =
  | {
      data: T;
      error: undefined;
      response: Response;
    }
  | {
      data: undefined;
      error: unknown;
      response: Response;
    };

function mapErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }
  const record = payload as Record<string, unknown>;
  if (Array.isArray(record.detail)) {
    for (const entry of record.detail) {
      if (typeof entry === 'string') {
        return entry;
      }
      if (entry && typeof entry === 'object') {
        const entryRecord = entry as Record<string, unknown>;
        if (typeof entryRecord.msg === 'string') return entryRecord.msg;
        if (typeof entryRecord.message === 'string') return entryRecord.message;
      }
    }
  }
  if (typeof record.detail === 'string') return record.detail;
  if (typeof record.message === 'string') return record.message;
  if (typeof record.error === 'string') return record.error;
  return fallback;
}

function unwrapSdkResult<T>(result: SdkFieldsResult<T>, fallbackMessage: string): T {
  if (result.error) {
    throw new UserProfileApiError(result.response.status, mapErrorMessage(result.error, fallbackMessage));
  }
  if (!result.data) {
    throw new UserProfileApiError(result.response.status ?? 500, fallbackMessage);
  }
  return result.data;
}

function assertSuccess<T extends { success?: boolean; message?: string }>(
  payload: T,
  fallbackMessage: string,
) {
  if (payload.success === false) {
    throw new UserProfileApiError(400, payload.message ?? fallbackMessage);
  }
}

function requireData<T>(payload: { data?: T | null }, fallbackMessage: string): T {
  if (payload.data == null) {
    throw new UserProfileApiError(500, fallbackMessage);
  }
  return payload.data;
}

export async function getCurrentUserProfile(): Promise<CurrentUserProfileResponseData> {
  if (USE_API_MOCK) {
    const meta = await getSessionMetaFromCookies();
    return {
      user_id: meta?.userId ?? '99999999-8888-7777-6666-555555555555',
      tenant_id: meta?.tenantId ?? '11111111-2222-3333-4444-555555555555',
      email: process.env.PLAYWRIGHT_TENANT_ADMIN_EMAIL ?? 'mock-admin@example.com',
      display_name: 'Mock Admin',
      role: 'admin',
      email_verified: true,
    };
  }

  const { client, auth } = await getServerApiClient();
  const result = await getCurrentUserProfileApiV1UsersMeGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<CurrentUserProfileSuccessResponse>,
    'Unable to load current user profile.',
  );
  assertSuccess(payload, 'Unable to load current user profile.');

  return requireData<CurrentUserProfileResponseData>(payload, 'Unable to load current user profile.');
}

export async function updateCurrentUserProfile(
  payload: UserProfileUpdateRequest,
): Promise<CurrentUserProfileResponseData> {
  const { client, auth } = await getServerApiClient();
  const result = await updateCurrentUserProfileApiV1UsersMeProfilePatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    body: payload,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<CurrentUserProfileSuccessResponse>,
    'Unable to update user profile.',
  );
  assertSuccess(response, 'Unable to update user profile.');

  return requireData<CurrentUserProfileResponseData>(response, 'Unable to update user profile.');
}

export async function changeCurrentUserEmail(
  payload: UserEmailChangeRequest,
): Promise<UserEmailChangeResponseData> {
  const { client, auth } = await getServerApiClient();
  const result = await changeCurrentUserEmailApiV1UsersMeEmailPatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    body: payload,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<UserEmailChangeSuccessResponse>,
    'Unable to change email address.',
  );
  assertSuccess(response, 'Unable to change email address.');

  return requireData<UserEmailChangeResponseData>(response, 'Unable to change email address.');
}

export async function disableCurrentUserAccount(
  payload: UserAccountDisableRequest,
): Promise<UserAccountDisableResponseData> {
  const { client, auth } = await getServerApiClient();
  const result = await disableCurrentUserAccountApiV1UsersMeDisablePost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    body: payload,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<UserAccountDisableSuccessResponse>,
    'Unable to disable account.',
  );
  assertSuccess(response, 'Unable to disable account.');

  return requireData<UserAccountDisableResponseData>(response, 'Unable to disable account.');
}

export async function listConsents(): Promise<ConsentView[]> {
  const { client, auth } = await getServerApiClient();
  const response = await listConsentsApiV1UsersConsentsGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
  });

  return response.data ?? [];
}

export async function recordConsent(payload: ConsentRequest): Promise<SuccessNoDataResponse> {
  const { client, auth } = await getServerApiClient();
  const response = await recordConsentApiV1UsersConsentsPost({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
  });

  return response.data ?? { success: true, message: 'Consent recorded', data: null };
}

export async function listNotificationPreferences(options?: {
  tenantId?: string | null;
  tenantRole?: string | null;
}): Promise<NotificationPreferenceView[]> {
  const headers: Record<string, string> = {};
  if (options?.tenantId) headers['X-Tenant-Id'] = options.tenantId;
  if (options?.tenantRole) headers['X-Tenant-Role'] = options.tenantRole;

  const { client, auth } = await getServerApiClient();
  const response = await listNotificationPreferencesApiV1UsersNotificationPreferencesGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    headers,
  });

  return response.data ?? [];
}

export async function upsertNotificationPreference(
  payload: NotificationPreferenceRequest,
  options?: { tenantId?: string | null; tenantRole?: string | null },
): Promise<NotificationPreferenceView> {
  const headers: Record<string, string> = {};
  if (options?.tenantId) headers['X-Tenant-Id'] = options.tenantId;
  if (options?.tenantRole) headers['X-Tenant-Role'] = options.tenantRole;

  const { client, auth } = await getServerApiClient();
  const response = await upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    body: payload,
    headers,
  });

  if (!response.data) {
    throw new UserProfileApiError(500, 'Notification preference response missing data.');
  }

  return response.data;
}
