import { NextResponse } from 'next/server';

import { getReadinessStatus } from '@/lib/server/services/health';

export async function GET() {
  try {
    const payload = await getReadinessStatus();
    return NextResponse.json(payload, { status: 200 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load backend readiness status.';
    return NextResponse.json({ message }, { status: 503 });
  }
}

