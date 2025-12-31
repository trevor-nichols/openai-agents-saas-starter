import { NextResponse, connection } from 'next/server';

import { fetchPlatformStatusSnapshot } from '@/lib/server/services/status';

export async function GET() {
  await connection();
  try {
    const statusSnapshot = await fetchPlatformStatusSnapshot();
    return NextResponse.json({ success: true, status: statusSnapshot }, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Unable to load platform status.';
    return NextResponse.json({ success: false, error: message }, { status: 502 });
  }
}
