import { NextRequest, NextResponse } from 'next/server';

import { getWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayEventsGet } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';
import { normalizeApiError } from '@/lib/server/apiError';

export async function GET(request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor') ?? undefined;
  const limitRaw = searchParams.get('limit');
  const limit = limitRaw ? Number(limitRaw) : undefined;

  try {
    const { client, auth } = await getServerApiClient();
    const response = await getWorkflowRunReplayEventsApiV1WorkflowsRunsRunIdReplayEventsGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: false,
      path: { run_id: runId },
      query: {
        cursor,
        limit,
      },
    });

    const status = response.response?.status ?? (response.error ? 500 : 204);
    if (response.error || status >= 400) {
      const err = response.error;
      const detail =
        typeof err === 'string'
          ? err
          : err && typeof err === 'object' && 'detail' in err && typeof (err as any).detail === 'string'
            ? (err as any).detail
            : undefined;
      return NextResponse.json(
        { message: detail ?? 'Failed to load workflow run replay', detail },
        { status },
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

