import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import {
  createPlatformTenant,
  listPlatformTenants,
  PlatformTenantsApiError,
} from '@/lib/server/services/platformTenants';
import type { PlatformTenantListFilters, TenantAccountStatus } from '@/types/tenantAccount';

import { requireOperatorSession } from '../_utils/auth';

const ALLOWED_STATUSES = new Set([
  'active',
  'suspended',
  'deprovisioning',
  'deprovisioned',
]);
const DEFAULT_LIMIT = 25;
const MAX_LIMIT = 200;

function parseLimit(raw: string | null): number | null {
  if (!raw) return DEFAULT_LIMIT;
  const value = Number.parseInt(raw, 10);
  if (Number.isNaN(value) || value <= 0) return null;
  return Math.min(value, MAX_LIMIT);
}

function parseOffset(raw: string | null): number | null {
  if (!raw) return 0;
  const value = Number.parseInt(raw, 10);
  if (Number.isNaN(value) || value < 0) return null;
  return value;
}

export async function GET(request: NextRequest) {
  const auth = await requireOperatorSession();
  if (!auth.ok) return auth.response;

  const url = new URL(request.url);
  const status = url.searchParams.get('status');
  const q = url.searchParams.get('q');
  const limit = parseLimit(url.searchParams.get('limit'));
  const offset = parseOffset(url.searchParams.get('offset'));

  if (status && !ALLOWED_STATUSES.has(status)) {
    return NextResponse.json(
      { success: false, error: 'status must be a valid tenant lifecycle state.' },
      { status: 400 },
    );
  }
  if (limit === null) {
    return NextResponse.json(
      { success: false, error: 'limit must be a positive integer.' },
      { status: 400 },
    );
  }
  if (offset === null) {
    return NextResponse.json(
      { success: false, error: 'offset must be a non-negative integer.' },
      { status: 400 },
    );
  }

  const filters: PlatformTenantListFilters = {
    status: status ? (status as TenantAccountStatus) : undefined,
    q: q ?? undefined,
    limit,
    offset,
  };

  try {
    const payload = await listPlatformTenants(filters);
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    if (error instanceof PlatformTenantsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load tenants.';
    return NextResponse.json({ message }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  const auth = await requireOperatorSession();
  if (!auth.ok) return auth.response;

  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json({ message: 'Invalid JSON payload.' }, { status: 400 });
  }

  if (!payload || typeof payload !== 'object' || typeof (payload as { name?: unknown }).name !== 'string') {
    return NextResponse.json({ message: 'name is required.' }, { status: 400 });
  }

  try {
    const tenant = await createPlatformTenant(payload as { name: string; slug?: string | null });
    return NextResponse.json(tenant, { status: 201 });
  } catch (error) {
    if (error instanceof PlatformTenantsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to create tenant.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
