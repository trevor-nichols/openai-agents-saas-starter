import { NextRequest, NextResponse } from 'next/server';

import { startTotpEnrollmentApiV1AuthMfaTotpEnrollPost } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(request: NextRequest) {
  try {
    const { client, auth } = await getServerApiClient();
    const url = new URL(request.url);
    const label = url.searchParams.get('label');
    const res = await startTotpEnrollmentApiV1AuthMfaTotpEnrollPost({
      client,
      auth,
      throwOnError: true,
      query: label ? { label } : undefined,
    });
    return NextResponse.json(res.data, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to start TOTP enrollment.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
