import { NextResponse } from 'next/server';

import { verifyTotpApiV1AuthMfaTotpVerifyPost } from '@/lib/api/client/sdk.gen';
import type { TotpVerifyRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as TotpVerifyRequest;
    const { client, auth } = await getServerApiClient();
    const res = await verifyTotpApiV1AuthMfaTotpVerifyPost({
      client,
      auth,
      throwOnError: true,
      body: payload,
    });
    return NextResponse.json(res.data ?? { message: 'ok' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to verify TOTP.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
