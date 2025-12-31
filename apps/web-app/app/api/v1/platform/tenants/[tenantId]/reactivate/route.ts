import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import {
  PlatformTenantsApiError,
  reactivatePlatformTenant,
} from '@/lib/server/services/platformTenants';

import { requireOperatorSession } from '../../../_utils/auth';

interface RouteContext {
  params: {
    tenantId: string;
  };
}

export async function POST(request: NextRequest, context: RouteContext) {
  const auth = await requireOperatorSession();
  if (!auth.ok) return auth.response;

  const tenantId = context.params.tenantId;
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ message: 'Invalid JSON payload.' }, { status: 400 });
  }

  const reason = (payload as { reason?: unknown } | null)?.reason;
  if (typeof reason !== 'string' || !reason.trim()) {
    return NextResponse.json({ message: 'reason is required.' }, { status: 400 });
  }

  try {
    const tenant = await reactivatePlatformTenant(tenantId, { reason: reason.trim() });
    return NextResponse.json(tenant, { status: 200 });
  } catch (error) {
    if (error instanceof PlatformTenantsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to reactivate tenant.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
