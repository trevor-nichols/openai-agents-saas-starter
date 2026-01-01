import 'server-only';

import {
  createTenantApiV1PlatformTenantsPost,
  deprovisionTenantApiV1PlatformTenantsTenantIdDeprovisionPost,
  getTenantApiV1PlatformTenantsTenantIdGet,
  listTenantsApiV1PlatformTenantsGet,
  reactivateTenantApiV1PlatformTenantsTenantIdReactivatePost,
  suspendTenantApiV1PlatformTenantsTenantIdSuspendPost,
  updateTenantApiV1PlatformTenantsTenantIdPatch,
} from '@/lib/api/client/sdk.gen';
import type {
  TenantAccountCreateRequest,
  TenantAccountLifecycleRequest,
  TenantAccountListResponse,
  TenantAccountOperatorResponse,
  TenantAccountUpdateRequest,
} from '@/lib/api/client/types.gen';
import type {
  PlatformTenantListFilters,
  TenantAccountCreateInput,
  TenantAccountLifecycleInput,
  TenantAccountListResult,
  TenantAccountOperatorSummary,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

import { getServerApiClient } from '../apiClient';

export class PlatformTenantsApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'PlatformTenantsApiError';
  }
}

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

const DEFAULT_LIMIT = 25;
const MAX_LIMIT = 200;

function clampLimit(value?: number | null): number {
  if (typeof value !== 'number' || Number.isNaN(value)) return DEFAULT_LIMIT;
  if (value <= 0) return DEFAULT_LIMIT;
  return Math.min(value, MAX_LIMIT);
}

function clampOffset(value?: number | null): number {
  if (typeof value !== 'number' || Number.isNaN(value) || value < 0) return 0;
  return value;
}

function mapErrorMessage(payload: unknown, fallback: string): string {
  if (!payload || typeof payload !== 'object') {
    return fallback;
  }
  const record = payload as Record<string, unknown>;
  if (Array.isArray(record.detail)) {
    for (const entry of record.detail) {
      if (typeof entry === 'string') return entry;
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
    throw new PlatformTenantsApiError(
      result.response.status,
      mapErrorMessage(result.error, fallbackMessage),
    );
  }
  if (!result.data) {
    throw new PlatformTenantsApiError(result.response.status ?? 500, fallbackMessage);
  }
  return result.data;
}

function mapOperatorAccount(dto: TenantAccountOperatorResponse): TenantAccountOperatorSummary {
  return {
    id: dto.id,
    slug: dto.slug,
    name: dto.name,
    status: dto.status,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
    statusUpdatedAt: dto.status_updated_at ?? null,
    suspendedAt: dto.suspended_at ?? null,
    deprovisionedAt: dto.deprovisioned_at ?? null,
    statusReason: dto.status_reason ?? null,
    statusUpdatedBy: dto.status_updated_by ?? null,
  };
}

export async function listPlatformTenants(
  filters: PlatformTenantListFilters = {},
): Promise<TenantAccountListResult> {
  const limit = clampLimit(filters.limit);
  const offset = clampOffset(filters.offset);

  const { client, auth } = await getServerApiClient();
  const result = await listTenantsApiV1PlatformTenantsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    query: {
      status: filters.status ?? undefined,
      q: filters.q ?? undefined,
      limit,
      offset,
    },
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountListResponse>,
    'Unable to load tenants.',
  );

  return {
    accounts: payload.accounts.map(mapOperatorAccount),
    total: payload.total,
  };
}

export async function getPlatformTenant(
  tenantId: string,
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new PlatformTenantsApiError(400, 'Tenant id is required.');
  }
  const { client, auth } = await getServerApiClient();
  const result = await getTenantApiV1PlatformTenantsTenantIdGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    path: {
      tenant_id: tenantId,
    },
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountOperatorResponse>,
    'Unable to load tenant.',
  );

  return mapOperatorAccount(payload);
}

export async function createPlatformTenant(
  payload: TenantAccountCreateInput,
): Promise<TenantAccountOperatorSummary> {
  const { client, auth } = await getServerApiClient();
  const body: TenantAccountCreateRequest = {
    name: payload.name,
    slug: payload.slug ?? undefined,
  };
  const result = await createTenantApiV1PlatformTenantsPost({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    body,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountOperatorResponse>,
    'Unable to create tenant.',
  );

  return mapOperatorAccount(response);
}

export async function updatePlatformTenant(
  tenantId: string,
  payload: TenantAccountUpdateInput,
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new PlatformTenantsApiError(400, 'Tenant id is required.');
  }
  const { client, auth } = await getServerApiClient();
  const body: TenantAccountUpdateRequest = {
    name: payload.name ?? undefined,
    slug: payload.slug ?? undefined,
  };
  const result = await updateTenantApiV1PlatformTenantsTenantIdPatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: {
      'Content-Type': 'application/json',
    },
    path: {
      tenant_id: tenantId,
    },
    body,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountOperatorResponse>,
    'Unable to update tenant.',
  );

  return mapOperatorAccount(response);
}

async function postLifecycleAction(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
  action: 'suspend' | 'reactivate' | 'deprovision',
): Promise<TenantAccountOperatorSummary> {
  if (!tenantId) {
    throw new PlatformTenantsApiError(400, 'Tenant id is required.');
  }
  const { client, auth } = await getServerApiClient();
  const body: TenantAccountLifecycleRequest = {
    reason: payload.reason,
  };

  const base = {
    client,
    auth,
    responseStyle: 'fields' as const,
    throwOnError: false as const,
    headers: {
      'Content-Type': 'application/json',
    },
    path: {
      tenant_id: tenantId,
    },
    body,
  };

  const result =
    action === 'suspend'
      ? await suspendTenantApiV1PlatformTenantsTenantIdSuspendPost(base)
      : action === 'reactivate'
        ? await reactivateTenantApiV1PlatformTenantsTenantIdReactivatePost(base)
        : await deprovisionTenantApiV1PlatformTenantsTenantIdDeprovisionPost(base);

  const response = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountOperatorResponse>,
    'Unable to update tenant lifecycle.',
  );

  return mapOperatorAccount(response);
}

export async function suspendPlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, payload, 'suspend');
}

export async function reactivatePlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, payload, 'reactivate');
}

export async function deprovisionPlatformTenant(
  tenantId: string,
  payload: TenantAccountLifecycleInput,
): Promise<TenantAccountOperatorSummary> {
  return postLifecycleAction(tenantId, payload, 'deprovision');
}
