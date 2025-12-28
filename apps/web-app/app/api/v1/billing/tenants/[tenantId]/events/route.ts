import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { billingEnabled } from '@/lib/config/features';
import { listTenantBillingEvents } from '@/lib/server/services/billing';
import type { StripeEventStatus } from '@/lib/api/client/types.gen';
import {
  mapBillingErrorToStatus,
  resolveTenantId,
  resolveTenantRole,
  type BillingTenantRouteContext,
} from '../../_utils';

const VALID_PROCESSING_STATUSES: StripeEventStatus[] = ['received', 'processed', 'failed'];

function normalizeProcessingStatus(value: string | null): StripeEventStatus | null {
  if (!value) {
    return null;
  }
  return VALID_PROCESSING_STATUSES.includes(value as StripeEventStatus)
    ? (value as StripeEventStatus)
    : null;
}

export async function GET(request: NextRequest, context: BillingTenantRouteContext) {
  if (!billingEnabled) {
    return NextResponse.json({ success: false, error: 'Billing is disabled.' }, { status: 404 });
  }
  const tenantId = await resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const eventType = searchParams.get('event_type');
  const rawProcessingStatus = searchParams.get('processing_status') ?? searchParams.get('status');
  const processingStatus = normalizeProcessingStatus(rawProcessingStatus);
  if (rawProcessingStatus && !processingStatus) {
    return NextResponse.json(
      {
        message: `processing_status must be one of: ${VALID_PROCESSING_STATUSES.join(', ')}.`,
      },
      { status: 400 },
    );
  }

  const limit = limitParam ? Number(limitParam) : undefined;
  if (limit !== undefined && Number.isNaN(limit)) {
    return NextResponse.json({ message: 'Limit must be a number.' }, { status: 400 });
  }

  try {
    const history = await listTenantBillingEvents(tenantId, {
      limit,
      cursor,
      eventType,
      processingStatus,
      tenantRole: resolveTenantRole(request),
    });
    return NextResponse.json(history, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load billing events.';
    const statusCode = mapBillingErrorToStatus(message, { includeNotFound: true });
    return NextResponse.json({ message }, { status: statusCode });
  }
}
