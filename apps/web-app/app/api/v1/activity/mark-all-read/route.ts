import { NextResponse } from 'next/server';

import { markAllActivityRead } from '@/lib/server/services/activity';

export async function POST() {
  try {
    const result = await markAllActivityRead();
    if (!result.ok) {
      return NextResponse.json(
        result.payload ?? { message: 'Failed to mark all as read.' },
        { status: result.status || 502 },
      );
    }

    return NextResponse.json(result.payload ?? { unread_count: 0 }, { status: result.status || 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to mark all as read.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 502;
    return NextResponse.json({ message }, { status });
  }
}
