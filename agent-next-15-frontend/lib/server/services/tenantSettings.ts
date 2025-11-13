'use server';

import { API_BASE_URL } from '@/lib/config';
import type { TenantSettingsResponseDto, TenantSettingsUpdateDto } from '@/types/tenantSettings';

import { getServerApiClient } from '../apiClient';

interface TenantSettingsOptions {
  tenantRole?: string | null;
}

function resolveBaseUrl(): string {
  return API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
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

async function authorizedFetch(
  path: string,
  init: RequestInit,
  options?: TenantSettingsOptions,
): Promise<Response> {
  const { auth } = await getServerApiClient();
  const token = auth();
  const headers = new Headers(init.headers);
  headers.set('Authorization', `Bearer ${token}`);
  if (options?.tenantRole) {
    headers.set('X-Tenant-Role', options.tenantRole);
  }
  return fetch(`${resolveBaseUrl()}${path}`, {
    ...init,
    headers,
    cache: 'no-store',
  });
}

export async function getTenantSettingsFromApi(
  options?: TenantSettingsOptions,
): Promise<TenantSettingsResponseDto> {
  const response = await authorizedFetch('/api/v1/tenants/settings', { method: 'GET' }, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new TenantSettingsApiError(response.status, mapErrorMessage(payload));
  }
  return payload as TenantSettingsResponseDto;
}

export async function updateTenantSettingsInApi(
  body: TenantSettingsUpdateDto,
  options?: TenantSettingsOptions,
): Promise<TenantSettingsResponseDto> {
  const response = await authorizedFetch(
    '/api/v1/tenants/settings',
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    },
    options,
  );
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new TenantSettingsApiError(response.status, mapErrorMessage(payload));
  }
  return payload as TenantSettingsResponseDto;
}
