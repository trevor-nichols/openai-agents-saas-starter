import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { cancelTenantSubscription } from '@/lib/server/services/billing';

interface RouteContext {
  params: {
    tenantId?: string;
  };
}

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

function resolveTenantId(context: RouteContext): string | null {
  return context.params.tenantId ?? null;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
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
    const subscription = await cancelTenantSubscription(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(subscription, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to cancel subscription.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
