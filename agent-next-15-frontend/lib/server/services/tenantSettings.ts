'use server';

import {
  getTenantSettingsApiV1TenantsSettingsGet,
  updateTenantSettingsApiV1TenantsSettingsPut,
} from '@/lib/api/client/sdk.gen';
import type { TenantSettingsResponse, TenantSettingsUpdateRequest } from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

interface TenantSettingsOptions {
  tenantRole?: string | null;
}

function mapErrorMessage(payload: unknown): string {
  if (!payload || typeof payload !== 'object') {
    return 'Tenant settings request failed.';
  }
  const record = payload as Record<string, unknown>;
  if (typeof record.detail === 'string') return record.detail;
  if (typeof record.message === 'string') return record.message;
  return 'Tenant settings request failed.';
}

export class TenantSettingsApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = 'TenantSettingsApiError';
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

function resolveHeaders(options?: TenantSettingsOptions): Headers | undefined {
  if (!options?.tenantRole) {
    return undefined;
  }
  const headers = new Headers();
  headers.set('X-Tenant-Role', options.tenantRole);
  return headers;
}

function unwrapSdkResult<T>(
  result: SdkFieldsResult<T>,
  fallbackMessage: string,
): T {
  if (result.error) {
    throw new TenantSettingsApiError(result.response.status, mapErrorMessage(result.error));
  }

  if (!result.data) {
    throw new TenantSettingsApiError(result.response.status ?? 500, fallbackMessage);
  }

  return result.data;
}

export async function getTenantSettingsFromApi(
  options?: TenantSettingsOptions,
): Promise<TenantSettingsResponse> {
  const { client, auth } = await getServerApiClient();
  const result = await getTenantSettingsApiV1TenantsSettingsGet({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: resolveHeaders(options),
  });

  return unwrapSdkResult(result as SdkFieldsResult<TenantSettingsResponse>, 'Tenant settings request failed.');
}

export async function updateTenantSettingsInApi(
  body: TenantSettingsUpdateRequest,
  options?: TenantSettingsOptions,
): Promise<TenantSettingsResponse> {
  const { client, auth } = await getServerApiClient();
  const result = await updateTenantSettingsApiV1TenantsSettingsPut({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: resolveHeaders(options),
    body,
  });

  return unwrapSdkResult(result as SdkFieldsResult<TenantSettingsResponse>, 'Tenant settings request failed.');
}
