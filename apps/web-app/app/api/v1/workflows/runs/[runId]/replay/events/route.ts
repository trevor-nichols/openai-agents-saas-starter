import { NextRequest, NextResponse } from 'next/server';

import { normalizeApiError } from '@/lib/server/apiError';
import { getWorkflowRunReplayEvents } from '@/lib/server/services/workflows';

export async function GET(request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor') ?? undefined;
  const limitRaw = searchParams.get('limit');
  const limit = limitRaw ? Number(limitRaw) : undefined;

  try {
    const response = await getWorkflowRunReplayEvents({
      runId,
      cursor: cursor ?? undefined,
      limit,
    });

    if (response.error || response.status >= 400) {
      return NextResponse.json(
        {
          message: response.error?.message ?? 'Failed to load workflow run replay',
          detail: response.error?.detail,
        },
        { status: response.status },
      );
    }

    if (!response.data) {
      return NextResponse.json({ message: 'Workflow run replay not found' }, { status: 404 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}
