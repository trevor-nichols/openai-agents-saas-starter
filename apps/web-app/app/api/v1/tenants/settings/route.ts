import type { NextRequest } from 'next/server';
import { NextResponse } from 'next/server';

import {
  TenantSettingsApiError,
  getTenantSettingsFromApi,
  updateTenantSettingsInApi,
} from '@/lib/server/services/tenantSettings';

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
    const settings = await getTenantSettingsFromApi({ tenantRole: resolveTenantRole(request) });
    return NextResponse.json(settings, { status: 200 });
  } catch (error) {
    if (error instanceof TenantSettingsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const authError = resolveAuthError(error);
    if (authError) {
      return NextResponse.json({ message: authError.message }, { status: authError.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to load tenant settings.';
    return NextResponse.json({ message }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const payload = await request.json();
    const ifMatch = request.headers.get('if-match');
    if (!ifMatch) {
      return NextResponse.json({ message: 'Missing If-Match header.' }, { status: 428 });
    }
    const settings = await updateTenantSettingsInApi(payload, {
      tenantRole: resolveTenantRole(request),
      ifMatch,
    });
    return NextResponse.json(settings, { status: 200 });
  } catch (error) {
    if (error instanceof TenantSettingsApiError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    const authError = resolveAuthError(error);
    if (authError) {
      return NextResponse.json({ message: authError.message }, { status: authError.status });
    }
    const message = error instanceof Error ? error.message : 'Failed to update tenant settings.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
