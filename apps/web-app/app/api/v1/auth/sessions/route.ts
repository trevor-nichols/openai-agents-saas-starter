import { NextRequest, NextResponse } from 'next/server';

import { listUserSessions } from '@/lib/server/services/auth/sessions';

function parseBoolean(value: string | null): boolean | undefined {
  if (value === null) return undefined;
  if (value === 'true') return true;
  if (value === 'false') return false;
  return undefined;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 500;
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const includeRevoked = parseBoolean(url.searchParams.get('include_revoked'));
  const limitParam = url.searchParams.get('limit');
  const offsetParam = url.searchParams.get('offset');
  const tenantId = url.searchParams.get('tenant_id');

  const limit = limitParam ? Number.parseInt(limitParam, 10) : undefined;
  const offset = offsetParam ? Number.parseInt(offsetParam, 10) : undefined;

  try {
    const payload = await listUserSessions({
      includeRevoked,
      limit,
      offset,
      tenantId,
    });
    return NextResponse.json(
      {
        success: true,
        ...payload,
      },
      { status: 200 },
    );
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load sessions.';
    const status = mapErrorToStatus(message);
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}

