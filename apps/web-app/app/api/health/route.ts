import { NextResponse } from 'next/server';

import { getHealthStatus } from '@/lib/server/services/health';

export async function GET() {
  try {
    const payload = await getHealthStatus();
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load backend health status.';
    return NextResponse.json({ message }, { status: 503 });
  }
}

