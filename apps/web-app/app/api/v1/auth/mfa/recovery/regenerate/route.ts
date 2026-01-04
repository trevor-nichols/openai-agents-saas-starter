import { NextResponse } from 'next/server';

import { regenerateRecoveryCodes } from '@/lib/server/services/auth/mfa';

export async function POST() {
  try {
    const res = await regenerateRecoveryCodes();
    return NextResponse.json(res, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to regenerate recovery codes.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 400;
    return NextResponse.json({ message }, { status });
  }
}
