import { NextRequest, NextResponse } from 'next/server';

const backendBase =
  process.env.NEXT_PUBLIC_API_URL ||
  process.env.API_URL ||
  process.env.BACKEND_API_URL ||
  'http://localhost:8000';

export async function POST(req: NextRequest) {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  const body = await req.text();
  const response = await fetch(`${backendBase}/api/v1/test-fixtures/apply`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body,
    cache: 'no-store',
  });

  const text = await response.text();
  const contentType = response.headers.get('content-type') || '';
  const isJson = contentType.includes('application/json');

  return new NextResponse(isJson ? text : text || response.statusText, {
    status: response.status,
    headers: {
      'content-type': isJson ? 'application/json' : 'text/plain',
    },
  });
}
