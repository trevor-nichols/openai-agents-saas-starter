import { NextRequest, NextResponse } from 'next/server';

import { registerTenant } from '@/lib/server/services/auth/signup';
import type { UserRegisterResponse } from '@/lib/api/client/types.gen';
import { persistSessionCookies } from '@/lib/auth/cookies';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('invalid') || normalized.includes('password')) {
    return 400;
  }
  return 500;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const response = await registerTenant(payload);

    const session: UserRegisterResponse = response;
    await persistSessionCookies({
      access_token: session.access_token,
      refresh_token: session.refresh_token,
      token_type: session.token_type ?? 'bearer',
      expires_at: session.expires_at,
      refresh_expires_at: session.refresh_expires_at,
      kid: session.kid,
      refresh_kid: session.refresh_kid,
      scopes: session.scopes,
      tenant_id: session.tenant_id,
      user_id: session.user_id,
    });

    return NextResponse.json(session, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to register tenant.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

