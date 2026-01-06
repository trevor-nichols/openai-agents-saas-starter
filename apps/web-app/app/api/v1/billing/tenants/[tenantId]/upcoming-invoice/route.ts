import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { FeatureFlagsApiError, requireBillingFeature } from '@/lib/server/features';
import { previewTenantUpcomingInvoice } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

export async function POST(request: NextRequest, context: BillingTenantRouteContext) {
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  try {
    await requireBillingFeature();
    const payload = await request.json();
    const preview = await previewTenantUpcomingInvoice(tenantId, payload, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(preview, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to preview upcoming invoice.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
