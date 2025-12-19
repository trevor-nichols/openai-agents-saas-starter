import type { CurrentUserProfileResponseData } from '@/lib/api/client/types.gen';
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

export async function fetchCurrentUserProfile(): Promise<CurrentUserProfileResponseData> {
  const response = await fetch(apiV1Path('/users/me'), { cache: 'no-store' });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createError(
      response,
      'Unable to load current user profile.',
      typeof payload?.message === 'string' ? payload.message : undefined,
    );
  }
  return parseJson<CurrentUserProfileResponseData>(response);
}
