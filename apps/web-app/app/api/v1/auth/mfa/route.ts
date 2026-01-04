import { NextResponse } from 'next/server';

import { listMfaMethods } from '@/lib/server/services/auth/mfa';

export async function GET() {
  try {
    const res = await listMfaMethods();
    return NextResponse.json(res ?? []);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load MFA methods.';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
