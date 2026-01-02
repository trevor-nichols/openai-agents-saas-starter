import { NextRequest, NextResponse } from 'next/server';

import { listSsoProvidersApiV1AuthSsoProvidersGet } from '@/lib/api/client/sdk.gen';
import { createApiClient } from '@/lib/server/apiClient';
import { normalizeApiError } from '@/lib/server/apiError';

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
    const client = createApiClient();
    const response = await listSsoProvidersApiV1AuthSsoProvidersGet({
      client,
      responseStyle: 'fields',
      throwOnError: true,
      query: {
        tenant_id: tenantId ?? undefined,
        tenant_slug: tenantSlug ?? undefined,
      },
    });

    return NextResponse.json(response.data ?? { providers: [] }, { status: 200 });
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}
