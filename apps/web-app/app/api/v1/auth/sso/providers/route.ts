import { NextRequest, NextResponse } from 'next/server';

import { normalizeApiError } from '@/lib/server/apiError';
import { listSsoProviders } from '@/lib/server/services/auth/sso';

function validateTenantSelector(tenantId: string | null, tenantSlug: string | null) {
  if (!tenantId && !tenantSlug) {
    return { status: 400, message: 'tenant_id or tenant_slug is required.' };
  }
  if (tenantId && tenantSlug) {
    return { status: 409, message: 'Provide either tenant_id or tenant_slug, not both.' };
  }
  return null;
}

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const tenantId = searchParams.get('tenant_id');
  const tenantSlug = searchParams.get('tenant_slug');

  const selectorError = validateTenantSelector(tenantId, tenantSlug);
  if (selectorError) {
    return NextResponse.json({ message: selectorError.message }, { status: selectorError.status });
  }

  try {
    const response = await listSsoProviders({ tenantId, tenantSlug });
    return NextResponse.json(response ?? { providers: [] }, { status: 200 });
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}
