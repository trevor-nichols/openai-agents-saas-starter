import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import {
  getTenantSubscription,
  startTenantSubscription,
  updateTenantSubscription,
} from '@/lib/server/services/billing';

interface RouteContext {
  params: {
    tenantId?: string;
  };
}

function resolveTenantId(context: RouteContext): string | null {
  const tenantId = context.params.tenantId;
  if (!tenantId) {
    return null;
  }
  return tenantId;
}

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
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

export async function GET(request: NextRequest, context: RouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const subscription = await getTenantSubscription(tenantId, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(subscription, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load subscription.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
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
    const subscription = await startTenantSubscription(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(subscription, { status: 201 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to start subscription.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const payload = await request.json();
    const subscription = await updateTenantSubscription(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(subscription, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to update subscription.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
