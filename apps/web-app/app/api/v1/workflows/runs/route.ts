import { NextResponse } from 'next/server';

import { listWorkflowRuns } from '@/lib/server/services/workflows';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const response = await listWorkflowRuns({
      workflowKey: searchParams.get('workflow_key'),
      runStatus: searchParams.get('run_status'),
      startedBefore: searchParams.get('started_before'),
      startedAfter: searchParams.get('started_after'),
      conversationId: searchParams.get('conversation_id'),
      cursor: searchParams.get('cursor'),
      limit: searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined,
    });

    return NextResponse.json(response ?? { items: [], next_cursor: null });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to load workflow runs';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
