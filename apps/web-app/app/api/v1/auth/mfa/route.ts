import { NextResponse } from 'next/server';

import { listMfaMethodsApiV1AuthMfaGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listMfaMethodsApiV1AuthMfaGet({ client, auth, throwOnError: true });
    return NextResponse.json(res.data ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load MFA methods.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
