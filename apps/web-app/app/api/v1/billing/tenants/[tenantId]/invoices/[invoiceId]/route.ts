import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { FeatureFlagsApiError, requireBillingFeature } from '@/lib/server/features';
import { getTenantInvoice } from '@/lib/server/services/billing';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../../_utils';

interface RouteContext extends BillingTenantRouteContext {
  params: Promise<{
    tenantId?: string;
    invoiceId?: string;
  }>;
}

async function resolveInvoiceId(context: RouteContext): Promise<string | null> {
  const { invoiceId } = await context.params;
  return invoiceId ?? null;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const tenantId = await resolveTenantId(context);
  const invoiceId = await resolveInvoiceId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }
  if (!invoiceId) {
    return NextResponse.json({ message: 'Invoice id is required.' }, { status: 400 });
  }

  try {
    await requireBillingFeature();
    const invoice = await getTenantInvoice(tenantId, invoiceId, {
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(invoice, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load invoice.';
    const status =
      error instanceof FeatureFlagsApiError
        ? error.status
        : mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
