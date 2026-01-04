import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { isBillingEnabled } from '@/lib/server/features';
import { listTenantInvoices } from '@/lib/server/services/billing';
import { parseOptionalLimit } from '@/app/api/v1/_utils/pagination';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

function parseOptionalOffset(raw: string | null): number | undefined | { error: string } {
  if (!raw) {
    return undefined;
  }
  const value = Number.parseInt(raw, 10);
  if (!Number.isFinite(value) || Number.isNaN(value) || value < 0) {
    return { error: 'offset must be a non-negative integer' };
  }
  return value;
}

export async function GET(request: NextRequest, context: BillingTenantRouteContext) {
  if (!(await isBillingEnabled())) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }

  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const parsedLimit = parseOptionalLimit(searchParams.get('limit'));
  if (!parsedLimit.ok) {
    return NextResponse.json({ message: parsedLimit.error }, { status: 400 });
  }
  const offset = parseOptionalOffset(searchParams.get('offset'));
  if (typeof offset === 'object') {
    return NextResponse.json({ message: offset.error }, { status: 400 });
  }

  try {
    const invoices = await listTenantInvoices(tenantId, {
      limit: parsedLimit.value,
      offset,
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(invoices, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load invoices.';
    const status = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status });
  }
}
