import { NextRequest, NextResponse } from 'next/server';

import {
  StatusSubscriptionServiceError,
  unsubscribeStatusSubscriptionViaToken,
} from '@/lib/server/services/statusSubscriptions';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const token = body?.token;
    const subscriptionId = body?.subscriptionId;
    if (!token || typeof token !== 'string' || !subscriptionId || typeof subscriptionId !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Unsubscribe token and subscription id are required.' },
        { status: 400 }
      );
    }

    await unsubscribeStatusSubscriptionViaToken({
      subscriptionId,
      token,
    });

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    const status =
      error instanceof StatusSubscriptionServiceError ? error.status : 500;
    const message =
      error instanceof Error ? error.message : 'Unable to unsubscribe.';

    return NextResponse.json({ success: false, error: message }, { status });
  }
}
