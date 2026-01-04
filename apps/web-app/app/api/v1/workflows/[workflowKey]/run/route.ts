import { NextResponse } from 'next/server';

import type { WorkflowRunRequestBody } from '@/lib/api/client/types.gen';
import { runWorkflow } from '@/lib/server/services/workflows';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ workflowKey: string }> },
) {
  const { workflowKey } = await params;
  try {
    const payload = (await request.json()) as WorkflowRunRequestBody;
    const response = await runWorkflow(workflowKey, payload);
    return NextResponse.json(response);
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to start workflow';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
