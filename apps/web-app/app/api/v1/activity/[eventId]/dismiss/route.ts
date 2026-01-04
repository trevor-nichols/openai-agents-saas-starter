import { NextResponse } from 'next/server';

import { dismissActivity } from '@/lib/server/services/activity';

type RouteParams = { params: Promise<{ eventId: string }> };

export async function POST(_request: Request, { params }: RouteParams) {
  const { eventId } = await params;
  if (!eventId) {
    return NextResponse.json({ message: 'Event id is required.' }, { status: 400 });
  }

  try {
    const result = await dismissActivity(eventId);
    if (!result.ok) {
      return NextResponse.json(
        result.payload ?? { message: 'Failed to dismiss activity.' },
        { status: result.status || 502 },
      );
    }

    return NextResponse.json(result.payload ?? { unread_count: 0 }, { status: result.status || 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to dismiss activity.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
