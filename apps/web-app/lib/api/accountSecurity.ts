import type {
  PasswordChangeRequest,
  PasswordResetRequest,
  SuccessNoDataResponse,
} from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

export async function changePasswordRequest(
  payload: PasswordChangeRequest,
): Promise<SuccessNoDataResponse> {
  const response = await fetch(apiV1Path('/auth/password/change'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const data = await parseJson<SuccessNoDataResponse | { message?: string }>(response);

  if (!response.ok) {
    const message = 'message' in data && data.message ? data.message : 'Failed to change password.';
    throw new Error(message);
  }

  return data as SuccessNoDataResponse;
}

export async function adminResetPasswordRequest(
  payload: PasswordResetRequest,
): Promise<SuccessNoDataResponse> {
  const response = await fetch(apiV1Path('/auth/password/reset'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const data = await parseJson<SuccessNoDataResponse | { message?: string }>(response);

  if (!response.ok) {
    const message =
      'message' in data && data.message
        ? data.message
        : 'Failed to reset password.';
    throw new Error(message);
  }

  return data as SuccessNoDataResponse;
}
