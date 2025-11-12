import { NextRequest, NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config';

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

    const url = new URL(
      `/api/v1/status/subscriptions/${encodeURIComponent(subscriptionId)}`,
      API_BASE_URL
    );
    url.searchParams.set('token', token);

    const response = await fetch(url, {
      method: 'DELETE',
      cache: 'no-store',
    });

    if (response.status === 204) {
      return NextResponse.json({ success: true }, { status: 200 });
    }

    const payload = await response.json().catch(() => null);
    return NextResponse.json(payload ?? {}, { status: response.status });
  } catch (_error) {
    return NextResponse.json(
      { success: false, error: 'Unable to unsubscribe.' },
      { status: 500 }
    );
  }
}
