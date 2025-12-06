import { NextResponse } from 'next/server';

import { confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost } from '@/lib/api/client/sdk.gen';
import type { StatusSubscriptionChallengeRequest } from '@/lib/api/client/types.gen';
import { createApiClient } from '@/lib/server/apiClient';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as StatusSubscriptionChallengeRequest;
    const client = createApiClient();
    const res = await confirmWebhookChallengeApiV1StatusSubscriptionsChallengePost({
      client,
      responseStyle: 'fields',
      throwOnError: true,
      headers: { 'Content-Type': 'application/json' },
      body: payload,
    });

    return NextResponse.json(res.data ?? {}, { status: res.response.status ?? 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to confirm webhook challenge.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
