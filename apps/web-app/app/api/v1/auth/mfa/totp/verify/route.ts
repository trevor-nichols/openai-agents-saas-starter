import { NextResponse } from 'next/server';

import type { TotpVerifyRequest } from '@/lib/api/client/types.gen';
import { verifyTotp } from '@/lib/server/services/auth/mfa';

export async function POST(request: Request) {
  try {
    const payload = (await request.json()) as TotpVerifyRequest;
    const res = await verifyTotp(payload);
    return NextResponse.json(res ?? { message: 'ok' });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to verify TOTP.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
