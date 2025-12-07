import { NextResponse } from 'next/server';

import { listConsentsApiV1UsersConsentsGet, recordConsentApiV1UsersConsentsPost } from '@/lib/api/client/sdk.gen';
import type { ConsentRequest } from '@/lib/api/client/types.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function GET() {
  try {
    const { client, auth } = await getServerApiClient();
    const res = await listConsentsApiV1UsersConsentsGet({ client, auth, throwOnError: true });
    return NextResponse.json(res.data ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load consents.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as ConsentRequest;
    const { client, auth } = await getServerApiClient();
    const res = await recordConsentApiV1UsersConsentsPost({
      client,
      auth,
      throwOnError: true,
      body: payload,
    });
    return NextResponse.json(res.data, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to record consent.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
