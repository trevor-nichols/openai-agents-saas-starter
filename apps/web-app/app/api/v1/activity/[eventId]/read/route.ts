import { NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config/server';
import { getAccessTokenFromCookies } from '@/lib/auth/cookies';

type RouteParams = { params: Promise<{ eventId: string }> };

export async function POST(_request: Request, { params }: RouteParams) {
  const token = await getAccessTokenFromCookies();
  if (!token) {
    return NextResponse.json({ message: 'Missing access token.' }, { status: 401 });
  }

  const { eventId } = await params;
  if (!eventId) {
    return NextResponse.json({ message: 'Event id is required.' }, { status: 400 });
  }

  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;
  try {
    const response = await fetch(`${baseUrl}/api/v1/activity/${eventId}/read`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const payload = await response.json().catch(() => ({}));
    if (!response.ok) {
      const status = response.status || 502;
      return NextResponse.json(payload ?? { message: 'Failed to mark activity as read.' }, { status });
    }

    return NextResponse.json(payload ?? { unread_count: 0 }, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to mark activity as read.';
    return NextResponse.json({ message }, { status: 502 });
  }
}
