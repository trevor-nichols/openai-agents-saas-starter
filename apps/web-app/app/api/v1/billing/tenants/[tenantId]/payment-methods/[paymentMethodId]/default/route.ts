import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { setTenantDefaultPaymentMethod } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../../../_utils';

interface RouteContext extends BillingTenantRouteContext {
  params: Promise<{
    tenantId?: string;
    paymentMethodId?: string;
  }>;
}

async function resolvePaymentMethodId(context: RouteContext): Promise<string | null> {
  const { paymentMethodId } = await context.params;
  return paymentMethodId ?? null;
}

export async function POST(request: NextRequest, context: RouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
  const paymentMethodId = await resolvePaymentMethodId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }
  if (!paymentMethodId) {
    return NextResponse.json({ message: 'Payment method id is required.' }, { status: 400 });
  }

  try {
    const response = await setTenantDefaultPaymentMethod(tenantId, paymentMethodId, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to set default payment method.';
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
