import { NextRequest, NextResponse } from 'next/server';

import { StatusSubscriptionServiceError, verifyStatusSubscriptionToken } from '@/lib/server/services/statusSubscriptions';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json().catch(() => null);
    const token = body?.token;

    if (!token || typeof token !== 'string') {
      return NextResponse.json(
        { success: false, error: 'Verification token is required.' },
        { status: 400 }
      );
    }

    const payload = await verifyStatusSubscriptionToken(token);
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const status =
      error instanceof StatusSubscriptionServiceError ? error.status : 500;
    const message =
      error instanceof Error ? error.message : 'Unable to verify subscription.';
    return NextResponse.json({ success: false, error: message }, { status });
  }
}
