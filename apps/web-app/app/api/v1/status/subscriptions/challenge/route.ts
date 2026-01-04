import { NextResponse } from 'next/server';

import type { StatusSubscriptionChallengeRequest } from '@/lib/api/client/types.gen';
import { confirmStatusSubscriptionChallenge } from '@/lib/server/services/statusSubscriptions';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as StatusSubscriptionChallengeRequest;
    const res = await confirmStatusSubscriptionChallenge(payload);
    return NextResponse.json(res.data ?? {}, { status: res.status ?? 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to confirm webhook challenge.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
