import { NextResponse } from 'next/server';

import { listGuardrailPresets } from '@/lib/server/services/guardrails';

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
    return 401;
  }
  return 500;
}

export async function GET() {
  try {
    const presets = await listGuardrailPresets();
    return NextResponse.json(
      {
        success: true,
        presets,
      },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load guardrail presets.';
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
