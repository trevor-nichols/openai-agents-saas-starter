import { NextResponse } from 'next/server';

import { regenerateRecoveryCodesApiV1AuthMfaRecoveryRegeneratePost } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await regenerateRecoveryCodesApiV1AuthMfaRecoveryRegeneratePost({
      client,
      auth,
      throwOnError: true,
    });
    return NextResponse.json(res.data, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to regenerate recovery codes.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
