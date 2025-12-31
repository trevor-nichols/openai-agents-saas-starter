import 'server-only';

import {
  getTenantAccountApiV1TenantsAccountGet,
  updateTenantAccountApiV1TenantsAccountPatch,
} from '@/lib/api/client/sdk.gen';
import type {
  TenantAccountResponse,
  TenantAccountSelfUpdateRequest,
} from '@/lib/api/client/types.gen';
import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

import { getServerApiClient } from '../apiClient';

export class TenantAccountApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'TenantAccountApiError';
  }
}

interface TenantAccountOptions {
  tenantRole?: string | null;
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
    throw new TenantAccountApiError(
      result.response.status,
      mapErrorMessage(result.error, fallbackMessage),
    );
  }
  if (!result.data) {
    throw new TenantAccountApiError(result.response.status ?? 500, fallbackMessage);
  }
  return result.data;
}

function mapTenantAccount(dto: TenantAccountResponse): TenantAccount {
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
  };
}

function resolveHeaders(options?: TenantAccountOptions): Headers | undefined {
  if (!options?.tenantRole) return undefined;
  const headers = new Headers();
  headers.set('X-Tenant-Role', options.tenantRole);
  return headers;
}

export async function getTenantAccountFromApi(
  options?: TenantAccountOptions,
): Promise<TenantAccount> {
  const { client, auth } = await getServerApiClient();
  const result = await getTenantAccountApiV1TenantsAccountGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: resolveHeaders(options),
  });

  const payload = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountResponse>,
    'Unable to load tenant account.',
  );

  return mapTenantAccount(payload);
}

export async function updateTenantAccountInApi(
  payload: TenantAccountSelfUpdateInput,
  options?: TenantAccountOptions,
): Promise<TenantAccount> {
  const { client, auth } = await getServerApiClient();
  const body: TenantAccountSelfUpdateRequest = {
    name: payload.name,
  };
  const result = await updateTenantAccountApiV1TenantsAccountPatch({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: resolveHeaders(options),
    body,
  });

  const response = unwrapSdkResult(
    result as SdkFieldsResult<TenantAccountResponse>,
    'Unable to update tenant account.',
  );

  return mapTenantAccount(response);
}
