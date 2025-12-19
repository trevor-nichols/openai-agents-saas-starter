import { NextResponse } from 'next/server';

import { getGuardrailPreset } from '@/lib/server/services/guardrails';

interface RouteContext {
  params: Promise<{
    presetKey?: string;
  }>;
}

function resolveErrorStatus(message: string): number {
  const normalized = message.toLowerCase();
  if (normalized.includes('missing access token') || normalized.includes('missing credentials')) {
    return 401;
  }
  if (normalized.includes('not found')) {
    return 404;
  }
  return 500;
}

export async function GET(_req: Request, context: RouteContext) {
  const { presetKey } = await context.params;
  if (!presetKey) {
    return NextResponse.json({ success: false, error: 'Preset key is required.' }, { status: 400 });
  }

  try {
    const preset = await getGuardrailPreset(presetKey);
    return NextResponse.json(
      { success: true, preset },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load guardrail preset.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ success: false, error: message }, { status });
  }
}
