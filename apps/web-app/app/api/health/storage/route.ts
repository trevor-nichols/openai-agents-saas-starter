import { NextResponse } from 'next/server';

import { getStorageHealthStatus } from '@/lib/server/services/health';

export async function GET() {
  try {
    const payload = await getStorageHealthStatus();
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load storage health status.';
    return NextResponse.json({ message }, { status: 503 });
  }
}
