import { NextRequest, NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config';

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

    const response = await fetch(`${API_BASE_URL}/api/v1/status/subscriptions/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token }),
      cache: 'no-store',
    });

    const payload = await response.json().catch(() => null);
    return NextResponse.json(payload ?? {}, { status: response.status });
  } catch (_error) {
    return NextResponse.json(
      { success: false, error: 'Unable to verify subscription.' },
      { status: 500 }
    );
  }
}
