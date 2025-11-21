import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { openBillingStream } from '@/lib/server/services/billing';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
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
