import { NextResponse } from 'next/server';

import { listGuardrails } from '@/lib/server/services/guardrails';

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
    return 401;
  }
  return 500;
}

export async function GET() {
  try {
    const guardrails = await listGuardrails();
    return NextResponse.json(
      {
        success: true,
        guardrails,
      },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load guardrails.';
    const status = resolveErrorStatus(message);
    return NextResponse.json(
      {
        success: false,
        error: message,
      },
      { status },
    );
  }
}
