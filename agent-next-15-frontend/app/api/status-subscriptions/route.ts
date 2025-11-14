import { NextResponse } from 'next/server';

import type { StatusSubscriptionCreateRequest } from '@/lib/api/client/types.gen';
import {
  StatusSubscriptionServiceError,
  createStatusSubscription,
} from '@/lib/server/services/statusSubscriptions';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as StatusSubscriptionCreateRequest;
    const authMode = payload.channel === 'webhook' ? 'session' : 'public';
    const subscription = await createStatusSubscription(payload, { authMode });
    return NextResponse.json(subscription, { status: 201 });
  } catch (error) {
    if (error instanceof StatusSubscriptionServiceError) {
      return NextResponse.json({ message: error.message }, { status: error.status });
    }
    if (error instanceof Error && error.message === 'Missing access token') {
      return NextResponse.json({ message: 'Authentication required.' }, { status: 401 });
    }
    const message = error instanceof Error ? error.message : 'Unable to subscribe to alerts.';
    return NextResponse.json({ message }, { status: 500 });
  }
}
