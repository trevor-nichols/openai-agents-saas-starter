import { NextResponse } from 'next/server';

import { completeMfaChallengeApiV1AuthMfaCompletePost } from '@/lib/api/client/sdk.gen';
import type { MfaChallengeCompleteRequest, UserSessionResponse } from '@/lib/api/client/types.gen';
import { createApiClient } from '@/lib/server/apiClient';
import { persistSessionFromResponse } from '@/lib/auth/session';

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
      await persistSessionFromResponse(tokens);
    }
    // Do not return tokens in the body; cookies hold the session.
    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to complete MFA challenge.';
    const status = message.toLowerCase().includes('validation') ? 400 : 401;
    return NextResponse.json({ message }, { status });
  }
}
