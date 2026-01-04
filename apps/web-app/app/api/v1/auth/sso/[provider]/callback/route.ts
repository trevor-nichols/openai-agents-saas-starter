import { NextResponse } from 'next/server';

import type { SsoCallbackRequest, UserSessionResponse } from '@/lib/api/client/types.gen';
import { isMfaChallengeResponse, resolveSafeRedirect } from '@/lib/auth/sso';
import { clearSsoRedirectCookie, readSsoRedirectCookie } from '@/lib/auth/ssoCookies';
import { persistSessionFromResponse } from '@/lib/auth/session';
import { normalizeApiError } from '@/lib/server/apiError';
import { completeSso } from '@/lib/server/services/auth/sso';

export async function POST(request: Request, context: { params: Promise<{ provider: string }> }) {
  const { provider } = await context.params;

  let payload: SsoCallbackRequest;
  try {
    payload = (await request.json()) as SsoCallbackRequest;
  } catch (_error) {
    return NextResponse.json({ message: 'Invalid JSON payload.' }, { status: 400 });
  }

  if (!payload?.code || !payload?.state) {
    return NextResponse.json({ message: 'code and state are required.' }, { status: 400 });
  }

  try {
    const response = await completeSso(provider, payload);
    const data = response.data;
    if (!data) {
      return NextResponse.json({ message: 'SSO callback returned empty response.' }, { status: 502 });
    }

    const redirectCookie = await readSsoRedirectCookie();
    const redirectTarget = resolveSafeRedirect(redirectCookie) ?? '/dashboard';
    await clearSsoRedirectCookie();

    if (isMfaChallengeResponse(data)) {
      return NextResponse.json(
        {
          status: 'mfa_required',
          redirect_to: redirectTarget,
          mfa: data,
        },
        { status: response.status ?? 202 },
      );
    }

    await persistSessionFromResponse(data as UserSessionResponse);
    return NextResponse.json(
      {
        status: 'authenticated',
        redirect_to: redirectTarget,
      },
      { status: 200 },
    );
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}
