import { NextRequest, NextResponse } from 'next/server';

import { startTotpEnrollment } from '@/lib/server/services/auth/mfa';

export async function POST(request: NextRequest) {
  try {
    const url = new URL(request.url);
    const label = url.searchParams.get('label');
    const res = await startTotpEnrollment({ label });
    return NextResponse.json(res, { status: 201 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to start TOTP enrollment.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
