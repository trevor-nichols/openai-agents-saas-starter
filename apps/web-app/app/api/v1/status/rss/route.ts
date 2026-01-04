import { NextResponse } from 'next/server';

import { fetchStatusRss } from '@/lib/server/services/status';

export async function GET() {
  try {
    const rss = await fetchStatusRss();

    return new Response(rss.body, {
      status: rss.status,
      headers: {
        'Content-Type': rss.contentType,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to load status RSS feed.';
    return NextResponse.json({ message }, { status: 502 });
  }
}
