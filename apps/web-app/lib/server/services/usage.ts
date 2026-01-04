'use server';

import { listUsageApiV1UsageGet } from '@/lib/api/client/sdk.gen';
import type { UsageCounterView } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '../apiClient';

export interface UsageListOptions {
  tenantId?: string | null;
  tenantRole?: string | null;
}

export async function listUsage(options?: UsageListOptions): Promise<UsageCounterView[]> {
  const { client, auth } = await getServerApiClient();
  const headers: Record<string, string> = {};
  if (options?.tenantId) headers['X-Tenant-Id'] = options.tenantId;
  if (options?.tenantRole) headers['X-Tenant-Role'] = options.tenantRole;

  const response = await listUsageApiV1UsageGet({
    client,
    auth,
    throwOnError: true,
    responseStyle: 'fields',
    headers,
  });

  return response.data ?? [];
}
