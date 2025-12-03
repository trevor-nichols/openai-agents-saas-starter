import { NextRequest, NextResponse } from 'next/server';

import {
  deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete,
  getWorkflowRunApiV1WorkflowsRunsRunIdGet,
} from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';
import { normalizeApiError } from '@/lib/server/apiError';

export async function GET(_request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  try {
    const { client, auth } = await getServerApiClient();
    const response = await getWorkflowRunApiV1WorkflowsRunsRunIdGet({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: false,
      path: { run_id: runId },
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
      return NextResponse.json({ message: detail ?? 'Failed to load workflow run', detail }, { status });
    }

    if (!response.data) {
      return NextResponse.json({ message: 'Workflow run not found' }, { status: 404 });
    }

    return NextResponse.json(response.data);
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json(body, { status });
  }
}

export async function DELETE(request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const { searchParams } = new URL(request.url);
  const hard = searchParams.get('hard') === 'true';
  const reason = searchParams.get('reason') ?? undefined;

  try {
    const { client, auth } = await getServerApiClient();
    const response = await deleteWorkflowRunApiV1WorkflowsRunsRunIdDelete({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: false,
      path: { run_id: runId },
      query: { hard, reason },
    });

    const upstreamStatus = response.response?.status;
    const status = upstreamStatus ?? (response.error ? 500 : 204);

    if (response.error || status >= 400) {
      const err = response.error;
      const detail =
        typeof err === 'string'
          ? err
          : err && typeof err === 'object' && 'detail' in err && typeof (err as any).detail === 'string'
            ? (err as any).detail
            : undefined;

      return NextResponse.json(
        {
          message: detail ?? 'Failed to delete workflow run',
          detail: detail ?? undefined,
        },
        { status },
      );
    }

    // Surface a consistent 204 regardless of upstream "204 vs 200" differences when deletion succeeds.
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json({ ...body, detail: body.detail ?? body.message }, { status });
  }
}
