import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { FeatureFlagsApiError, requireBillingFeature } from '@/lib/server/features';
import { changeTenantSubscriptionPlan } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../../_utils';

export async function POST(request: NextRequest, context: BillingTenantRouteContext) {
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    await requireBillingFeature();
    const payload = await request.json();
    const planChange = await changeTenantSubscriptionPlan(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(planChange, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to change subscription plan.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
