import type { UsageCounterView } from '@/lib/api/client/types.gen';
import { apiV1Path } from '@/lib/apiPaths';

async function parseJson<T>(response: Response): Promise<T> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    throw new Error('Failed to parse response from server.');
  }
}

function buildHeaders(tenantId?: string | null, tenantRole?: string | null): HeadersInit {
  const headers: Record<string, string> = {};
  if (tenantId) headers['X-Tenant-Id'] = tenantId;
  if (tenantRole) headers['X-Tenant-Role'] = tenantRole;
  return headers;
}

export async function listUsageRequest(options?: {
  tenantId?: string | null;
  tenantRole?: string | null;
}): Promise<UsageCounterView[]> {
  const response = await fetch(apiV1Path('/usage'), {
    headers: buildHeaders(options?.tenantId, options?.tenantRole),
    cache: 'no-store',
  });
  const data = await parseJson<UsageCounterView[] | { message?: string }>(response);
  if (!response.ok) {
    throw new Error((data as { message?: string }).message ?? 'Failed to load usage.');
  }
  return data as UsageCounterView[];
}
