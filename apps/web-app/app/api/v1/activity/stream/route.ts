import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { openActivityStream } from '@/lib/server/services/activity';

export async function GET(request: NextRequest) {
  try {
    return await openActivityStream({ signal: request.signal });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to open activity stream.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
