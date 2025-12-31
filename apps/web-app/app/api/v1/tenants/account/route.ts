import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import {
  getTenantAccountFromApi,
  TenantAccountApiError,
  updateTenantAccountInApi,
} from '@/lib/server/services/tenantAccount';

function resolveTenantRole(request: NextRequest): string | null {
  return request.headers.get('x-tenant-role');
}

function resolveAuthError(error: unknown): { status: number; message: string } | null {
  if (error instanceof Error) {
    const normalized = error.message.toLowerCase();
    if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
      return { status: 401, message: error.message };
    }
  }
  return null;
}

export async function GET(request: NextRequest) {
  try {
    const tenantRole = resolveTenantRole(request);
    const account = await getTenantAccountFromApi(tenantRole ? { tenantRole } : undefined);
    return NextResponse.json(account, { status: 200 });
  } catch (error) {
    if (error instanceof TenantAccountApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const authError = resolveAuthError(error);
    if (authError) {
      return NextResponse.json({ message: authError.message }, { status: authError.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load tenant account.';
    return NextResponse.json({ message }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
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
    const tenantRole = resolveTenantRole(request);
    const account = await updateTenantAccountInApi(
      { name: (payload as { name: string }).name },
      tenantRole ? { tenantRole } : undefined,
    );
    return NextResponse.json(account, { status: 200 });
  } catch (error) {
    if (error instanceof TenantAccountApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const authError = resolveAuthError(error);
    if (authError) {
      return NextResponse.json({ message: authError.message }, { status: authError.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to update tenant account.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
