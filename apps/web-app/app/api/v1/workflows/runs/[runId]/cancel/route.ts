import { NextResponse } from 'next/server';

import { cancelWorkflowRunApiV1WorkflowsRunsRunIdCancelPost } from '@/lib/api/client/sdk.gen';
import { getServerApiClient } from '@/lib/server/apiClient';

export async function POST(_: Request, { params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  try {
    const { client, auth } = await getServerApiClient();
    await cancelWorkflowRunApiV1WorkflowsRunsRunIdCancelPost({
      client,
      auth,
      responseStyle: 'fields',
      throwOnError: true,
      path: { run_id: runId },
    });

    return NextResponse.json({ success: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to cancel workflow run';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
