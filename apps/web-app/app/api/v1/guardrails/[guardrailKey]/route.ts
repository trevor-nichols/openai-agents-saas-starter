import { NextResponse } from 'next/server';

import { getGuardrail } from '@/lib/server/services/guardrails';

interface RouteContext {
  params: Promise<{
    guardrailKey?: string;
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
  const { guardrailKey } = await context.params;
  if (!guardrailKey) {
    return NextResponse.json({ success: false, error: 'Guardrail key is required.' }, { status: 400 });
  }

  try {
    const guardrail = await getGuardrail(guardrailKey);
    return NextResponse.json(
      { success: true, guardrail },
      { status: 200 },
    );
  } catch (error) {
    const message =
      error instanceof Error ? error.message : 'Failed to load guardrail.';
    const status = resolveErrorStatus(message);
    return NextResponse.json({ success: false, error: message }, { status });
  }
}
