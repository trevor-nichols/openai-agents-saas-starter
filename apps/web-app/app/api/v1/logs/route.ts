import { NextResponse, type NextRequest } from 'next/server';

import { API_BASE_URL } from '@/lib/config';

const BACKEND_LOG_ENDPOINT = `${API_BASE_URL}/api/v1/logs`;

async function forwardToBackend(request: NextRequest, payload: unknown) {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const cookieHeader = request.headers.get('cookie');
  if (cookieHeader) headers.Cookie = cookieHeader;

  const authHeader = request.headers.get('authorization');
  if (authHeader) headers.Authorization = authHeader;

  return fetch(BACKEND_LOG_ENDPOINT, {
    method: 'POST',
    headers,
    body: JSON.stringify(payload),
    cache: 'no-store',
    redirect: 'manual',
  });
}

export async function POST(request: NextRequest) {
  let payload: unknown;
  try {
    payload = await request.json();
  } catch {
    return NextResponse.json(
      { success: false, error: 'Invalid JSON payload.' },
      { status: 400 },
    );
  }

  try {
    const upstream = await forwardToBackend(request, payload);
    const text = await upstream.text();
    let body: unknown = null;
    if (text) {
      try {
        body = JSON.parse(text);
      } catch {
        body = { message: text };
      }
    }
    const responseHeaders = new Headers();
    const retryAfter = upstream.headers.get('retry-after');
    if (retryAfter) responseHeaders.set('Retry-After', retryAfter);

    return NextResponse.json(body ?? { accepted: upstream.ok }, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error instanceof Error ? error.message : 'Failed to forward log.' },
      { status: 502 },
    );
  }
}
