import { NextRequest, NextResponse } from 'next/server';

import {
  listNotificationPreferencesApiV1UsersNotificationPreferencesGet,
  upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut,
} from '@/lib/api/client/sdk.gen';
import type { NotificationPreferenceRequest } from '@/lib/api/client/types.gen';
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
    const res = await listNotificationPreferencesApiV1UsersNotificationPreferencesGet({
      client,
      auth,
      throwOnError: true,
      headers: tenantHeaders(request),
    });
    return NextResponse.json(res.data ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load notification preferences.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const payload = (await request.json()) as NotificationPreferenceRequest;
    const { client, auth } = await getServerApiClient();
    const res = await upsertNotificationPreferenceApiV1UsersNotificationPreferencesPut({
      client,
      auth,
      throwOnError: true,
      body: payload,
      headers: tenantHeaders(request),
    });
    return NextResponse.json(res.data);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to save notification preference.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
