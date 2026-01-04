import { NextRequest, NextResponse } from 'next/server';

import type { NotificationPreferenceRequest } from '@/lib/api/client/types.gen';
import { listNotificationPreferences, upsertNotificationPreference } from '@/lib/server/services/users';

export async function GET(request: NextRequest) {
  try {
    const res = await listNotificationPreferences({
      tenantId: request.headers.get('x-tenant-id'),
      tenantRole: request.headers.get('x-tenant-role'),
    });
    return NextResponse.json(res ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load notification preferences.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const payload = (await request.json()) as NotificationPreferenceRequest;
    const res = await upsertNotificationPreference(payload, {
      tenantId: request.headers.get('x-tenant-id'),
      tenantRole: request.headers.get('x-tenant-role'),
    });
    return NextResponse.json(res);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to save notification preference.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
