import { apiV1Path } from '@/lib/apiPaths';
import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

function createError(response: Response, fallbackMessage: string, detail?: string): Error {
  const base =
    detail ||
    (response.status === 401
      ? 'You have been signed out. Please log back in.'
      : fallbackMessage);
  return new Error(base);
}

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse API response.');
  }
}

function extractErrorMessage(payload: unknown): string | undefined {
  if (!payload || typeof payload !== 'object') {
    return undefined;
  }
  const record = payload as Record<string, unknown>;
  const detail = record.message ?? record.error ?? record.detail;
  return typeof detail === 'string' ? detail : undefined;
}

export async function fetchTenantAccount(): Promise<TenantAccount> {
  const response = await fetch(apiV1Path('/tenants/account'), { cache: 'no-store' });
  const payload = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to load tenant account.', extractErrorMessage(payload));
  }

  return payload as TenantAccount;
}

export async function updateTenantAccount(
  payload: TenantAccountSelfUpdateInput,
): Promise<TenantAccount> {
  const response = await fetch(apiV1Path('/tenants/account'), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });

  const body = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to update tenant account.', extractErrorMessage(body));
  }

  return body as TenantAccount;
}
