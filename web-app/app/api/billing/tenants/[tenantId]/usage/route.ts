import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { recordTenantUsage } from '@/lib/server/services/billing';

interface RouteContext {
  params: {
    tenantId?: string;
  };
}

function resolveTenantId(context: RouteContext): string | null {
  return context.params.tenantId ?? null;
}

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 400;
}

export async function POST(request: NextRequest, context: RouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const payload = await request.json();
    await recordTenantUsage(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(
      {
        success: true,
        message: 'Usage recorded',
      },
      { status: 202 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to record usage.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
