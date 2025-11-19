import { NextRequest, NextResponse } from 'next/server';

import { adminResetPassword } from '@/lib/server/services/auth/passwords';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 500;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const response = await adminResetPassword(payload);
    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to reset password.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

