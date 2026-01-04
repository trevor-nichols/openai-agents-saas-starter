import { NextResponse } from 'next/server';

import { openWorkflowReplayStream } from '@/lib/server/services/workflows';

export async function GET(request: Request, context: { params: Promise<{ runId: string }> }) {
  const { runId } = await context.params;
  const { searchParams } = new URL(request.url);
  const cursor = searchParams.get('cursor') ?? undefined;

  try {
    const upstream = await openWorkflowReplayStream({
      runId,
      cursor,
      signal: request.signal,
    });

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
    const message = error instanceof Error ? error.message : 'Failed to stream workflow replay';
    const status = message.toLowerCase().includes('missing access token') ? 401 : 500;
    return NextResponse.json({ message }, { status });
  }
}
