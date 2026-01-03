import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { isBillingEnabled } from '@/lib/server/features';
import {
  getTenantSubscription,
  startTenantSubscription,
  updateTenantSubscription,
} from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

export async function GET(request: NextRequest, context: BillingTenantRouteContext) {
  if (!(await isBillingEnabled())) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
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
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: NextRequest, context: BillingTenantRouteContext) {
  if (!(await isBillingEnabled())) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
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
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}

export async function PATCH(request: NextRequest, context: BillingTenantRouteContext) {
  if (!(await isBillingEnabled())) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
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
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
