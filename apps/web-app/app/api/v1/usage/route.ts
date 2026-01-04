import { NextRequest, NextResponse } from 'next/server';

import { listUsage } from '@/lib/server/services/usage';

export async function GET(request: NextRequest) {
  try {
    const payload = await listUsage({
      tenantId: request.headers.get('x-tenant-id'),
      tenantRole: request.headers.get('x-tenant-role'),
    });
    return NextResponse.json(payload ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load usage.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
