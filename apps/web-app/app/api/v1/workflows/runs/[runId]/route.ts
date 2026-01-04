import { NextRequest, NextResponse } from 'next/server';

import { normalizeApiError } from '@/lib/server/apiError';
import { deleteWorkflowRun, getWorkflowRun } from '@/lib/server/services/workflows';

export async function GET(_request: NextRequest, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  try {
    const result = await getWorkflowRun(runId);
    if (result.error) {
      return NextResponse.json(
        { message: result.error.message, detail: result.error.detail },
        { status: result.status },
      );
    }

    if (!result.data) {
      return NextResponse.json({ message: 'Workflow run not found' }, { status: 404 });
    }

    return NextResponse.json(result.data);
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
    const response = await deleteWorkflowRun({ runId, hard, reason });
    if (response.error || response.status >= 400) {
      return NextResponse.json(
        {
          message: response.error?.message ?? 'Failed to delete workflow run',
          detail: response.error?.detail,
        },
        { status: response.status },
      );
    }

    // Surface a consistent 204 regardless of upstream "204 vs 200" differences when deletion succeeds.
    return new NextResponse(null, { status: 204 });
  } catch (error) {
    const { status, body } = normalizeApiError(error);
    return NextResponse.json({ ...body, detail: body.detail ?? body.message }, { status });
  }
}
