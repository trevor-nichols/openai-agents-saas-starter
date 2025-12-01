import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { revokeUserSession } from '@/lib/server/services/auth/sessions';

interface RouteContext {
  params: Promise<{
    sessionId: string;
  }>;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 500;
}

export async function DELETE(_request: NextRequest, context: RouteContext) {
  const { sessionId } = await context.params;
  if (!sessionId) {
    return NextResponse.json({ message: 'Session id is required.' }, { status: 400 });
  }

  try {
    const payload = await revokeUserSession(sessionId);
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to revoke session.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
