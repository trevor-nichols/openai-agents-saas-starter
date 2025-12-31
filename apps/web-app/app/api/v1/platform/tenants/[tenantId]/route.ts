import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import {
  getPlatformTenant,
  PlatformTenantsApiError,
  updatePlatformTenant,
} from '@/lib/server/services/platformTenants';

import { requireOperatorSession } from '../../_utils/auth';

interface RouteContext {
  params: {
    tenantId: string;
  };
}

export async function GET(_request: NextRequest, context: RouteContext) {
  const auth = await requireOperatorSession();
  if (!auth.ok) return auth.response;

  const tenantId = context.params.tenantId;
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const tenant = await getPlatformTenant(tenantId);
    return NextResponse.json(tenant, { status: 200 });
  } catch (error) {
    if (error instanceof PlatformTenantsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load tenant.';
    return NextResponse.json({ message }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest, context: RouteContext) {
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

  if (!payload || typeof payload !== 'object') {
    return NextResponse.json({ message: 'Payload must be an object.' }, { status: 400 });
  }

  const body = payload as { name?: string | null; slug?: string | null };
  if (body.name === undefined && body.slug === undefined) {
    return NextResponse.json({ message: 'At least one field is required.' }, { status: 400 });
  }

  try {
    const tenant = await updatePlatformTenant(tenantId, body);
    return NextResponse.json(tenant, { status: 200 });
  } catch (error) {
    if (error instanceof PlatformTenantsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to update tenant.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
