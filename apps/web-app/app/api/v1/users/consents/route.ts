import { NextResponse } from 'next/server';

import type { ConsentRequest } from '@/lib/api/client/types.gen';
import { listConsents, recordConsent } from '@/lib/server/services/users';

export async function GET() {
  try {
    const res = await listConsents();
    return NextResponse.json(res ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load consents.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as ConsentRequest;
    const res = await recordConsent(payload);
    return NextResponse.json(res, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to record consent.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
