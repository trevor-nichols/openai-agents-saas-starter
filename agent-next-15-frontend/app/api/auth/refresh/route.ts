import { NextResponse } from 'next/server';

import { getRefreshTokenFromCookies } from '@/lib/auth/cookies';
import { destroySession, refreshSessionWithBackend } from '@/lib/auth/session';

export async function POST() {
  const token = getRefreshTokenFromCookies();
  if (!token) {
    destroySession();
    return NextResponse.json({ message: 'Refresh token missing.' }, { status: 401 });
  }

  try {
    const updated = await refreshSessionWithBackend(token);
    return NextResponse.json({
      userId: updated.user_id,
      tenantId: updated.tenant_id,
      expiresAt: updated.expires_at,
    });
  } catch (error) {
    destroySession();
    return NextResponse.json(
      { message: error instanceof Error ? error.message : 'Failed to refresh session.' },
      { status: 401 },
    );
  }
}
