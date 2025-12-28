import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { createTenantSetupIntent } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../../_utils';

export async function POST(request: NextRequest, context: BillingTenantRouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    const payload = await request.json();
    const intent = await createTenantSetupIntent(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(intent, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to create setup intent.';
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
