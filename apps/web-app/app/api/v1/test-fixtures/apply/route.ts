import { NextRequest, NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config/server';

export async function POST(req: NextRequest) {
  if (process.env.NODE_ENV === 'production') {
    return NextResponse.json({ error: 'Not found' }, { status: 404 });
  }

  const body = await req.text();
  const response = await fetch(`${API_BASE_URL}/api/v1/test-fixtures/apply`, {
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
