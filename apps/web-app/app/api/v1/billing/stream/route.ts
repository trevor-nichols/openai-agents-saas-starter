import type { NextRequest } from 'next/server';

import { FeatureFlagsApiError, requireBillingStreamFeature } from '@/lib/server/features';
import { openBillingStream } from '@/lib/server/services/billing';

export async function GET(request: NextRequest) {
  try {
    await requireBillingStreamFeature();
    return await openBillingStream({
      signal: request.signal,
      tenantRole: request.headers.get('x-tenant-role'),
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to open billing stream.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : message.toLowerCase().includes('missing access token')
          ? 401
          : 502;
    return new Response(message, { status });
  }
}
