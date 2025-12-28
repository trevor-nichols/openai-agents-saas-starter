import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { changeTenantSubscriptionPlan } from '@/lib/server/services/billing';

interface RouteContext {
  params: Promise<{
    tenantId: string;
  }>;
}

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

async function resolveTenantId(context: RouteContext): Promise<string | null> {
  const { tenantId } = await context.params;
  return tenantId ?? null;
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  if (normalized.includes('already') || normalized.includes('conflict')) {
    return 409;
  }
  return 400;
}

export async function POST(request: NextRequest, context: RouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const payload = await request.json();
    const planChange = await changeTenantSubscriptionPlan(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(planChange, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to change subscription plan.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
