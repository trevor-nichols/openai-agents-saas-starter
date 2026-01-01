import { NextResponse } from 'next/server';

import { startSsoApiV1AuthSsoProviderStartPost } from '@/lib/api/client/sdk.gen';
import type { SsoStartRequest } from '@/lib/api/client/types.gen';
import { resolveSafeRedirect } from '@/lib/auth/sso';
import { clearSsoRedirectCookie, setSsoRedirectCookie } from '@/lib/auth/ssoCookies';
import { createApiClient } from '@/lib/server/apiClient';
import { normalizeApiError } from '@/lib/server/apiError';

type SsoStartPayload = SsoStartRequest & {
  redirect_to?: string | null;
};

function validateTenantSelector(payload: SsoStartRequest) {
  if (!payload.tenant_id && !payload.tenant_slug) {
    return { status: 400, message: 'tenant_id or tenant_slug is required.' };
  }
  if (payload.tenant_id && payload.tenant_slug) {
    return { status: 409, message: 'Provide either tenant_id or tenant_slug, not both.' };
  }
  return null;
}

export async function POST(request: Request, context: { params: Promise<{ provider: string }> }) {
  const { provider } = await context.params;

  let payload: SsoStartPayload;
  try {
    payload = (await request.json()) as SsoStartPayload;
  } catch (_error) {
    return NextResponse.json({ message: 'Invalid JSON payload.' }, { status: 400 });
  }

  const selectorError = validateTenantSelector(payload);
  if (selectorError) {
    return NextResponse.json({ message: selectorError.message }, { status: selectorError.status });
  }

  const redirectTarget = resolveSafeRedirect(payload.redirect_to ?? null);
  if (payload.redirect_to && !redirectTarget) {
    return NextResponse.json({ message: 'Invalid redirect target.' }, { status: 400 });
  }

  try {
    const client = createApiClient();
    const response = await startSsoApiV1AuthSsoProviderStartPost({
      client,
      responseStyle: 'fields',
      throwOnError: true,
      path: { provider },
      body: {
        tenant_id: payload.tenant_id ?? null,
        tenant_slug: payload.tenant_slug ?? null,
        login_hint: payload.login_hint ?? null,
      },
    });

    if (!response.data?.authorize_url) {
      return NextResponse.json({ message: 'SSO start returned empty response.' }, { status: 502 });
    }

    if (redirectTarget) {
      await setSsoRedirectCookie(redirectTarget);
    } else {
      await clearSsoRedirectCookie();
    }

    return NextResponse.json(response.data, { status: 200 });
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}
