import { NextRequest, NextResponse } from 'next/server';

import { getAccessTokenFromCookies } from '@/lib/auth/cookies';
import { API_BASE_URL, USE_API_MOCK } from '@/lib/config';

export async function POST(request: NextRequest) {
  const accessToken = getAccessTokenFromCookies();
  if (!accessToken) {
    return NextResponse.json({ message: 'Unauthorized' }, { status: 401 });
  }

  const payload = await request.json();

  if (USE_API_MOCK) {
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        const chunk = {
          chunk: 'Hello from mock agent! ',
          conversation_id: 'mock-conversation',
          is_complete: false,
        };
        controller.enqueue(encoder.encode(`data: ${JSON.stringify(chunk)}\n\n`));
        controller.enqueue(
          encoder.encode(
            `data: ${JSON.stringify({ ...chunk, chunk: 'Done.', is_complete: true })}\n\n`,
          ),
        );
        controller.close();
      },
    });
    return new NextResponse(stream, {
      status: 200,
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  }

  const backendResponse = await fetch(`${API_BASE_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'text/event-stream',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  });

  if (!backendResponse.ok || !backendResponse.body) {
    const message = await backendResponse.text();
    return NextResponse.json(
      { message: message || 'Failed to start stream.' },
      { status: backendResponse.status },
    );
  }

  return new NextResponse(backendResponse.body, {
    status: backendResponse.status,
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
}
