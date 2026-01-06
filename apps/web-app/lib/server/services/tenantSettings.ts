import 'server-only';
import {
  getTenantSettingsApiV1TenantsSettingsGet,
  updateTenantSettingsApiV1TenantsSettingsPut,
} from '@/lib/api/client/sdk.gen';
import type { TenantSettingsResponse, TenantSettingsUpdateRequest } from '@/lib/api/client/types.gen';

import { getServerApiClient } from '../apiClient';

interface TenantSettingsOptions {
  tenantRole?: string | null;
  ifMatch?: string | null;
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

function resolveHeaders(options?: TenantSettingsOptions): Record<string, string> | undefined {
  if (!options?.tenantRole && !options?.ifMatch) {
    return undefined;
  }
  const headers: Record<string, string> = {};
  if (options?.tenantRole) {
    headers['X-Tenant-Role'] = options.tenantRole;
  }
  if (options?.ifMatch) {
    headers['If-Match'] = options.ifMatch;
  }
  return headers;
}

function resolveRequiredIfMatchHeaders(
  options?: TenantSettingsOptions,
): { 'If-Match': string; 'X-Tenant-Role'?: string | null } {
  if (!options?.ifMatch) {
    throw new TenantSettingsApiError(428, 'Missing If-Match header.');
  }
  const headers: { 'If-Match': string; 'X-Tenant-Role'?: string | null } = {
    'If-Match': options.ifMatch,
  };
  if (options?.tenantRole) {
    headers['X-Tenant-Role'] = options.tenantRole;
  }
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
  options: TenantSettingsOptions & { ifMatch: string },
): Promise<TenantSettingsResponse> {
  const { client, auth } = await getServerApiClient();
  const result = await updateTenantSettingsApiV1TenantsSettingsPut({
    client,
    auth,
    responseStyle: 'fields',
    throwOnError: false,
    headers: resolveRequiredIfMatchHeaders(options),
    body,
  });

  return unwrapSdkResult(result as SdkFieldsResult<TenantSettingsResponse>, 'Tenant settings request failed.');
}
