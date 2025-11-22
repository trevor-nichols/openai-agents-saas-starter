import { NextRequest, NextResponse } from 'next/server';

import { getRefreshTokenFromCookies } from '@/lib/auth/cookies';
import { destroySession } from '@/lib/auth/session';
import { logoutSession } from '@/lib/server/services/auth/sessions';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 400;
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const refreshToken = body?.refresh_token ?? (await getRefreshTokenFromCookies());

    if (refreshToken) {
      await logoutSession({ refresh_token: refreshToken });
    }

    await destroySession();
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to logout.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ success: false, error: message }, { status });
  }
}
