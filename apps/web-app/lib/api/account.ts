import type { SuccessResponse } from '@/lib/api/client/types.gen';
import type { TenantSubscription } from '@/lib/types/billing';
import type { AccountSessionResponse } from '@/types/account';
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

export async function fetchAccountSession(): Promise<AccountSessionResponse> {
  const response = await fetch(apiV1Path('/auth/me'), { cache: 'no-store' });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createError(
      response,
      'Unable to load account profile.',
      typeof payload?.message === 'string' ? payload.message : undefined,
    );
  }
  return parseJson<AccountSessionResponse>(response);
}

export async function fetchTenantSubscriptionSummary(
  tenantId: string,
): Promise<TenantSubscription> {
  const response = await fetch(apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/subscription`), {
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createError(
      response,
      'Unable to load tenant subscription.',
      typeof payload?.message === 'string' ? payload.message : undefined,
    );
  }
  return parseJson<TenantSubscription>(response);
}

export async function resendVerificationEmailRequest(): Promise<SuccessResponse> {
  const response = await fetch(apiV1Path('/auth/email/send'), {
    method: 'POST',
    cache: 'no-store',
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw createError(
      response,
      'Unable to send verification email.',
      typeof payload?.message === 'string' ? payload.message : undefined,
    );
  }
  return parseJson<SuccessResponse>(response);
}
