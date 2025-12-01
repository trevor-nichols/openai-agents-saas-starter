import { NextRequest, NextResponse } from 'next/server';

import { requestPasswordReset } from '@/lib/server/services/auth/passwords';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  if (normalized.includes('email')) {
    return 400;
  }
  return 500;
}

export async function POST(request: NextRequest) {
  try {
    const payload = await request.json();
    const response = await requestPasswordReset(payload);
    return NextResponse.json(response, { status: 202 });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to request password reset.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

