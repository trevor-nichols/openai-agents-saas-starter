import { NextRequest, NextResponse } from 'next/server';

import { listUsageApiV1UsageGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

function tenantHeaders(request: NextRequest) {
  const headers: Record<string, string> = {};
  const tenantId = request.headers.get('x-tenant-id');
  const tenantRole = request.headers.get('x-tenant-role');
  if (tenantId) headers['X-Tenant-Id'] = tenantId;
  if (tenantRole) headers['X-Tenant-Role'] = tenantRole;
  return headers;
}

export async function GET(request: NextRequest) {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listUsageApiV1UsageGet({
      client,
      auth,
      throwOnError: true,
      headers: tenantHeaders(request),
    });
    return NextResponse.json(res.data ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load usage.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
