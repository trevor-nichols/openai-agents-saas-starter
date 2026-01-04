import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { isBillingEnabled } from '@/lib/server/features';
import { recordTenantUsage } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

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
    const status = mapBillingErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}
