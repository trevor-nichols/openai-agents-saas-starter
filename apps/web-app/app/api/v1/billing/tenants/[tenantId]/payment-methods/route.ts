import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { listTenantPaymentMethods } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

export async function GET(request: NextRequest, context: BillingTenantRouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const paymentMethods = await listTenantPaymentMethods(tenantId, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(paymentMethods, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load payment methods.';
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
