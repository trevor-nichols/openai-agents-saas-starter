import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { listTenantUsageTotals } from '@/lib/server/services/billing';
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

  const { searchParams } = new URL(request.url);
  const featureKeys = searchParams.getAll('feature_keys');
  const periodStart = searchParams.get('period_start');
  const periodEnd = searchParams.get('period_end');

  try {
    const totals = await listTenantUsageTotals(tenantId, {
      featureKeys: featureKeys.length ? featureKeys : undefined,
      periodStart: periodStart ?? undefined,
      periodEnd: periodEnd ?? undefined,
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(totals, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load usage totals.';
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
