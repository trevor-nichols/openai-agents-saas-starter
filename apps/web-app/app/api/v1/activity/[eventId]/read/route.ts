import { NextResponse } from 'next/server';

import { markActivityRead } from '@/lib/server/services/activity';

type RouteParams = { params: Promise<{ eventId: string }> };

export async function POST(_request: Request, { params }: RouteParams) {
  const { eventId } = await params;
  if (!eventId) {
    return NextResponse.json({ message: 'Event id is required.' }, { status: 400 });
  }

  try {
    const result = await markActivityRead(eventId);
    if (!result.ok) {
      return NextResponse.json(
        result.payload ?? { message: 'Failed to mark activity as read.' },
        { status: result.status || 502 },
      );
    }

    return NextResponse.json(result.payload ?? { unread_count: 0 }, { status: result.status || 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to mark activity as read.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
