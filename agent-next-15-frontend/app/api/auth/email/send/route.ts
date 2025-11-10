import { NextResponse } from 'next/server';

import { sendVerificationEmail } from '@/lib/server/services/auth/email';

function mapErrorToStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token')) {
    return 401;
  }
  return 500;
}

export async function POST() {
  try {
    const payload = await sendVerificationEmail();
    return NextResponse.json(payload, { status: 202 });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to send verification email.';
    const status = mapErrorToStatus(message);
    return NextResponse.json({ message }, { status });
  }
}

