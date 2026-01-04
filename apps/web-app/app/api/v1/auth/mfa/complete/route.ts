import { NextResponse } from 'next/server';

import type { MfaChallengeCompleteRequest, UserSessionResponse } from '@/lib/api/client/types.gen';
import { persistSessionFromResponse } from '@/lib/auth/session';
import { completeMfaChallenge } from '@/lib/server/services/auth/mfa';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as MfaChallengeCompleteRequest;
    const tokens = (await completeMfaChallenge(payload)) as UserSessionResponse | undefined;
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
