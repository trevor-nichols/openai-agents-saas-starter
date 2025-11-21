import { NextRequest, NextResponse } from 'next/server';

import { getSessionMetaFromCookies } from '@/lib/auth/cookies';
import { listStatusSubscriptions } from '@/lib/server/services/statusSubscriptions';

const REQUIRED_SCOPE = 'status:manage';
const DEFAULT_LIMIT = 25;

function parseLimit(raw: string | null): number | null {
  if (!raw) return DEFAULT_LIMIT;
  const value = Number.parseInt(raw, 10);
  if (Number.isNaN(value) || value <= 0) return null;
  return Math.min(value, 200);
}

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) return 401;
  if (normalized.includes('forbidden') || normalized.includes('status:manage')) return 403;
  if (normalized.includes('invalid cursor') || normalized.includes('limit')) return 400;
  return 500;
}

export async function GET(request: NextRequest) {
  const session = await getSessionMetaFromCookies();
  if (!session) {
    return NextResponse.json({ success: false, error: 'Missing access token.' }, { status: 401 });
  }
  if (!session.scopes?.includes(REQUIRED_SCOPE)) {
    return NextResponse.json(
      { success: false, error: 'Forbidden: status:manage scope required.' },
      { status: 403 },
    );
  }

  const url = new URL(request.url);
  const cursor = url.searchParams.get('cursor');
  const limit = parseLimit(url.searchParams.get('limit'));

  const hasTenantParam =
    url.searchParams.has('tenant_id') || url.searchParams.has('tenantId');
  const rawTenant = hasTenantParam
    ? url.searchParams.get('tenant_id') ?? url.searchParams.get('tenantId')
    : undefined;

  if (rawTenant === '') {
    return NextResponse.json(
      { success: false, error: 'tenant_id must be a valid UUID or "all".' },
      { status: 400 },
    );
  }

  const wantsAllTenants = rawTenant === 'all';

  let resolvedTenantId: string | null | undefined;
  if (hasTenantParam) {
    if (wantsAllTenants) {
      resolvedTenantId = null;
    } else {
      if (!rawTenant || !validateUuid(rawTenant)) {
        return NextResponse.json(
          { success: false, error: 'tenant_id must be a valid UUID or "all".' },
          { status: 400 },
        );
      }
      resolvedTenantId = rawTenant;
    }
  } else {
    resolvedTenantId = undefined;
  }

  // No tenant param specified: fall back to session tenant (if any) without elevating to all tenants.
  if (resolvedTenantId === undefined) {
    resolvedTenantId = session.tenantId ?? null;
  }

  if (limit === null) {
    return NextResponse.json(
      { success: false, error: 'limit must be a positive integer.' },
      { status: 400 },
    );
  }

  try {
    const payload = await listStatusSubscriptions({
      cursor: cursor || null,
      tenantId: resolvedTenantId,
      limit,
      includeAllTenants: wantsAllTenants,
    });

    return NextResponse.json(
      {
        success: true,
        items: payload.items,
        next_cursor: payload.next_cursor ?? null,
      },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unable to load status subscriptions.';
    return NextResponse.json(
      { success: false, error: message },
      { status: mapErrorToStatus(message) },
    );
  }
}

function validateUuid(candidate: string): boolean {
  return /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(candidate);
}
