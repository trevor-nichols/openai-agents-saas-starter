import { NextResponse, type NextRequest } from 'next/server';

import type { FrontendLogPayload } from '@/lib/api/client/types.gen';
import { forwardFrontendLog } from '@/lib/server/services/frontendLogs';

export async function POST(request: NextRequest) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid JSON payload.' },
      { status: 400 },
    );
  }

  try {
    const result = await forwardFrontendLog({
      payload: payload as FrontendLogPayload,
      authorization: request.headers.get('authorization'),
      cookie: request.headers.get('cookie'),
    });

    const responseHeaders = new Headers();
    if (result.retryAfter) responseHeaders.set('Retry-After', result.retryAfter);

    return NextResponse.json(result.body ?? { accepted: result.ok }, {
      status: result.status,
      headers: responseHeaders,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to forward log.' },
      { status: 502 },
    );
  }
}
