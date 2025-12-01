import { NextResponse } from 'next/server';

/**
 * Alias for /api/v1/status/rss to match backend `/status.rss`.
 */
export function GET(request: Request) {
  const target = new URL('/api/v1/status/rss', request.url);
  return NextResponse.redirect(target, 307);
}
