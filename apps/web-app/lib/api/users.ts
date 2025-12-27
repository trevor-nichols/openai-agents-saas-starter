import type {
  CurrentUserProfileResponseData,
  UserAccountDisableRequest,
  UserAccountDisableResponseData,
  UserEmailChangeRequest,
  UserEmailChangeResponseData,
  UserProfileUpdateRequest,
} from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse API response.');
  }
}

function createError(response: Response, fallbackMessage: string, detail?: string): Error {
  const base =
    detail ||
    (response.status === 401
      ? 'You have been signed out. Please log in again.'
      : fallbackMessage);
  return new Error(base);
}

function extractMessage(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined;
  }
  const record = payload as Record<string, unknown>;
  if (typeof record.message === 'string') {
    return record.message;
  }
  if (typeof record.detail === 'string') {
    return record.detail;
  }
  if (typeof record.error === 'string') {
    return record.error;
  }
  return undefined;
}

export async function fetchCurrentUserProfile(): Promise<CurrentUserProfileResponseData> {
  const response = await fetch(apiV1Path('/users/me'), { cache: 'no-store' });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createError(
      response,
      'Unable to load current user profile.',
      extractMessage(payload),
    );
  }
  return parseJson<CurrentUserProfileResponseData>(response);
}

export async function updateCurrentUserProfileRequest(
  payload: UserProfileUpdateRequest,
): Promise<CurrentUserProfileResponseData> {
  const response = await fetch(apiV1Path('/users/me/profile'), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw createError(response, 'Unable to update profile.', extractMessage(errorPayload));
  }
  return parseJson<CurrentUserProfileResponseData>(response);
}

export async function changeCurrentUserEmailRequest(
  payload: UserEmailChangeRequest,
): Promise<UserEmailChangeResponseData> {
  const response = await fetch(apiV1Path('/users/me/email'), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw createError(response, 'Unable to update email address.', extractMessage(errorPayload));
  }
  return parseJson<UserEmailChangeResponseData>(response);
}

export async function disableCurrentUserAccountRequest(
  payload: UserAccountDisableRequest,
): Promise<UserAccountDisableResponseData> {
  const response = await fetch(apiV1Path('/users/me/disable'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const errorPayload = await response.json().catch(() => ({}));
    throw createError(response, 'Unable to disable account.', extractMessage(errorPayload));
  }
  return parseJson<UserAccountDisableResponseData>(response);
}
