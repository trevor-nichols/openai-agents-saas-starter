import { apiV1Path } from '@/lib/apiPaths';
import type {
  PlatformTenantListFilters,
  TenantAccountCreateInput,
  TenantAccountLifecycleInput,
  TenantAccountListResult,
  TenantAccountOperatorSummary,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

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

function buildSearchParams(filters: PlatformTenantListFilters): URLSearchParams {
  const search = new URLSearchParams();
  if (filters.status) search.set('status', filters.status);
  if (filters.q) search.set('q', filters.q);
  if (typeof filters.limit === 'number') search.set('limit', String(filters.limit));
  if (typeof filters.offset === 'number') search.set('offset', String(filters.offset));
  return search;
}

export async function fetchPlatformTenants(
  filters: PlatformTenantListFilters = {},
): Promise<TenantAccountListResult> {
  const search = buildSearchParams(filters);
  const response = await fetch(
    apiV1Path(`/platform/tenants${search.size > 0 ? `?${search.toString()}` : ''}`),
    { cache: 'no-store' },
  );
  const payload = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to load tenants.', extractErrorMessage(payload));
  }

  return payload as TenantAccountListResult;
}

export async function fetchPlatformTenant(
  tenantId: string,
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  const response = await fetch(apiV1Path(`/platform/tenants/${encodeURIComponent(tenantId)}`), {
    cache: 'no-store',
  });
  const payload = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to load tenant.', extractErrorMessage(payload));
  }

  return payload as TenantAccountOperatorSummary;
}

export async function createPlatformTenant(
  payload: TenantAccountCreateInput,
): Promise<TenantAccountOperatorSummary> {
  const response = await fetch(apiV1Path('/platform/tenants'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  const body = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to create tenant.', extractErrorMessage(body));
  }

  return body as TenantAccountOperatorSummary;
}

export async function updatePlatformTenant(
  tenantId: string,
  payload: TenantAccountUpdateInput,
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  const response = await fetch(apiV1Path(`/platform/tenants/${encodeURIComponent(tenantId)}`), {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
    cache: 'no-store',
  });
  const body = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to update tenant.', extractErrorMessage(body));
  }

  return body as TenantAccountOperatorSummary;
}

async function postLifecycleAction(
  tenantId: string,
  action: 'suspend' | 'reactivate' | 'deprovision',
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new Error('Tenant id is required.');
  }
  const response = await fetch(
    apiV1Path(`/platform/tenants/${encodeURIComponent(tenantId)}/${action}`),
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
      cache: 'no-store',
    },
  );
  const body = await parseJson<unknown>(response);

  if (!response.ok) {
    throw createError(response, 'Unable to update tenant lifecycle.', extractErrorMessage(body));
  }

  return body as TenantAccountOperatorSummary;
}

export async function suspendPlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, 'suspend', payload);
}

export async function reactivatePlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, 'reactivate', payload);
}

export async function deprovisionPlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, 'deprovision', payload);
}
