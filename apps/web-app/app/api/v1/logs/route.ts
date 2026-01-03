import { NextResponse, type NextRequest } from 'next/server';
import { createHmac } from 'node:crypto';

import { ACCESS_TOKEN_COOKIE } from '@/lib/config';
import { API_BASE_URL } from '@/lib/config/server';

const BACKEND_LOG_ENDPOINT = `${API_BASE_URL}/api/v1/logs`;

function getCookieValue(cookieHeader: string, name: string): string | null {
  const parts = cookieHeader.split(';');
  for (const part of parts) {
    const [key, ...rest] = part.trim().split('=');
    if (!key) continue;
    if (key === name) {
      return rest.join('=') || null;
    }
  }
  return null;
}

function signBody(body: string): string | null {
  const secret = process.env.FRONTEND_LOG_SHARED_SECRET;
  if (!secret) return null;
  return createHmac('sha256', secret).update(body).digest('hex');
}

async function forwardToBackend(request: NextRequest, payload: unknown) {
  const body = JSON.stringify(payload);
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    Accept: 'application/json',
  };

  const authHeader = request.headers.get('authorization');
  if (authHeader) {
    headers.Authorization = authHeader;
  } else {
    const cookieHeader = request.headers.get('cookie');
    if (cookieHeader) {
      const accessToken = getCookieValue(cookieHeader, ACCESS_TOKEN_COOKIE);
      if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
    }
  }

  if (!headers.Authorization) {
    const signature = signBody(body);
    if (signature) headers['X-Log-Signature'] = signature;
  }

  return fetch(BACKEND_LOG_ENDPOINT, {
    method: 'POST',
    headers,
    body,
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
