import { NextResponse } from 'next/server';

import { completeMfaChallengeApiV1AuthMfaCompletePost } from '@/lib/api/client/sdk.gen';
import type { MfaChallengeCompleteRequest, UserSessionResponse } from '@/lib/api/client/types.gen';
import { createApiClient } from '@/lib/server/apiClient';
import { persistSessionCookies } from '@/lib/auth/cookies';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as MfaChallengeCompleteRequest;
    const client = createApiClient();
    const res = await completeMfaChallengeApiV1AuthMfaCompletePost({
      client,
      throwOnError: true,
      body: payload,
    });
    const tokens = res.data as UserSessionResponse | undefined;
    if (tokens) {
      await persistSessionCookies({
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        token_type: tokens.token_type ?? 'bearer',
        expires_at: tokens.expires_at,
        refresh_expires_at: tokens.refresh_expires_at,
        kid: tokens.kid,
        refresh_kid: tokens.refresh_kid,
        scopes: tokens.scopes,
        tenant_id: tokens.tenant_id,
        user_id: tokens.user_id,
      });
    }
    // Do not return tokens in the body; cookies hold the session.
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to complete MFA challenge.';
    const status = message.toLowerCase().includes('validation') ? 400 : 401;
    return NextResponse.json({ message }, { status });
  }
}
