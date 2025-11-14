import type { NextRequest } from 'next/server';

import { openBillingStream } from '@/lib/server/services/billing';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  try {
    return await openBillingStream({
      signal: request.signal,
      tenantRole: request.headers.get('x-tenant-role'),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to open billing stream.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return new Response(message, { status });
  }
}
