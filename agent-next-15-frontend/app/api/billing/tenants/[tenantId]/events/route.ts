import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import { listTenantBillingEvents } from '@/lib/server/services/billing';

interface RouteContext {
  params: {
    tenantId?: string;
  };
}

function resolveTenantId(context: RouteContext): string | null {
  return context.params.tenantId ?? null;
}

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 400;
}

export async function GET(request: NextRequest, context: RouteContext) {
  const tenantId = resolveTenantId(context);
  if (!tenantId) {
    return NextResponse.json({ message: 'Tenant id is required.' }, { status: 400 });
  }

  const { searchParams } = new URL(request.url);
  const limitParam = searchParams.get('limit');
  const cursor = searchParams.get('cursor');
  const eventType = searchParams.get('event_type');
  const processingStatus =
    searchParams.get('processing_status') ?? searchParams.get('status');

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
    const statusCode = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status: statusCode });
  }
}
