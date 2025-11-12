import { NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config';

export async function GET() {
  try {
    const upstream = await fetch(`${API_BASE_URL}/api/v1/status/rss`, { cache: 'no-store' });
    const body = await upstream.text();
    const contentType = upstream.headers.get('content-type') ?? 'application/rss+xml; charset=utf-8';

    return new Response(body, {
      status: upstream.status,
      headers: {
        'Content-Type': contentType,
      },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Unable to load status RSS feed.';
    return NextResponse.json({ message }, { status: 502 });
  }
}
