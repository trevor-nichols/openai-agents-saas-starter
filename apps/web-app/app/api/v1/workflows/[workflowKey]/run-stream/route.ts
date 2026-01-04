import { NextResponse } from 'next/server';

import type { WorkflowRunRequestBody } from '@/lib/api/client/types.gen';
import { openWorkflowStream } from '@/lib/server/services/workflows';

export async function POST(
  request: Request,
  { params }: { params: Promise<{ workflowKey: string }> },
) {
  const { workflowKey } = await params;
  try {
    const payload = (await request.json()) as WorkflowRunRequestBody;
    const upstream = await openWorkflowStream(workflowKey, payload, request.signal);

    const headers = new Headers({
      'Content-Type': 'text/event-stream',
      Connection: 'keep-alive',
      'Cache-Control': 'no-cache',
    });

    const contentType = upstream.contentType;
    if (contentType) {
      headers.set('Content-Type', contentType);
    }

    return new Response(upstream.stream, {
      status: upstream.status,
      headers,
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Failed to stream workflow';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
