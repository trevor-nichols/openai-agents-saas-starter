import { NextResponse } from 'next/server';

import { destroySession } from '@/lib/auth/session';
import { logoutAllSessions } from '@/lib/server/services/auth/sessions';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 400;
}

export async function POST() {
  try {
    await logoutAllSessions();
    await destroySession();
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to logout all sessions.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ success: false, error: message }, { status });
  }
}

