import { NextResponse } from 'next/server';

import { submitContact, MarketingServiceError } from '@/lib/server/services/marketing';

export async function POST(request: Request) {
  const payload = await request
    .json()
    .catch(() => null) as
    | {
        name?: string | null;
        email?: string | null;
        company?: string | null;
        topic?: string | null;
        message?: string | null;
        honeypot?: string | null;
      }
    | null;

  if (!payload) {
    return NextResponse.json({ success: false, error: 'Request body is required.' }, { status: 400 });
  }

  const email = payload.email?.trim() ?? '';
  const message = payload.message?.trim() ?? '';

  if (!email || !message) {
    return NextResponse.json(
      { success: false, error: 'Email and message are required.' },
      { status: 400 },
    );
  }

  if (payload.honeypot && payload.honeypot.trim().length > 0) {
    // Silent hard block for spam submissions
    return NextResponse.json({ success: true }, { status: 202 });
  }

  try {
    await submitContact({
      name: payload.name,
      email,
      company: payload.company,
      topic: payload.topic,
      message,
      honeypot: payload.honeypot,
    });

    return NextResponse.json({ success: true }, { status: 202 });
  } catch (error) {
    const resolvedError =
      error instanceof MarketingServiceError
        ? error
        : new MarketingServiceError('Unable to submit contact request.', 500);

    return NextResponse.json(
      { success: false, error: resolvedError.message },
      { status: resolvedError.status },
    );
  }
}

