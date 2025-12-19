import type {
  MfaChallengeCompleteRequest,
  MfaMethodView,
  RecoveryCodesResponse,
  TotpEnrollResponse,
  TotpVerifyRequest,
} from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

export async function listMfaMethodsRequest(): Promise<MfaMethodView[]> {
  const response = await fetch(apiV1Path('/auth/mfa'), { cache: 'no-store' });
  const data = await parseJson<MfaMethodView[] | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to load MFA methods.');
  }
  return data as MfaMethodView[];
}

export async function startTotpEnrollmentRequest(label?: string | null): Promise<TotpEnrollResponse> {
  const base = apiV1Path('/auth/mfa/totp/enroll');
  const path = label ? `${base}?label=${encodeURIComponent(label)}` : base;
  const response = await fetch(path, { method: 'POST', cache: 'no-store' });
  const data = await parseJson<TotpEnrollResponse | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to start TOTP enrollment.');
  }
  return data as TotpEnrollResponse;
}

export async function verifyTotpRequest(payload: TotpVerifyRequest): Promise<void> {
  const response = await fetch(apiV1Path('/auth/mfa/totp/verify'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const data = await parseJson<{ message?: string }>(response).catch(() => ({}));
    const message = 'message' in data && data.message ? data.message : 'Failed to verify TOTP.';
    throw new Error(message);
  }
}

export async function revokeMfaMethodRequest(methodId: string): Promise<void> {
  const response = await fetch(apiV1Path(`/auth/mfa/${methodId}`), {
    method: 'DELETE',
    cache: 'no-store',
  });
  if (!response.ok) {
    const data = await parseJson<{ message?: string }>(response).catch(() => ({}));
    const message = 'message' in data && data.message ? data.message : 'Failed to revoke MFA method.';
    throw new Error(message);
  }
}

export async function regenerateRecoveryCodesRequest(): Promise<RecoveryCodesResponse> {
  const response = await fetch(apiV1Path('/auth/mfa/recovery/regenerate'), {
    method: 'POST',
    cache: 'no-store',
  });
  const data = await parseJson<RecoveryCodesResponse | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to regenerate recovery codes.');
  }
  return data as RecoveryCodesResponse;
}

export async function completeMfaChallengeRequest(
  payload: MfaChallengeCompleteRequest,
): Promise<void> {
  const response = await fetch(apiV1Path('/auth/mfa/complete'), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  if (!response.ok) {
    const data = await parseJson<{ message?: string }>(response).catch(() => ({}));
    throw new Error((data as { message?: string }).message ?? 'Failed to complete MFA challenge.');
  }
}
