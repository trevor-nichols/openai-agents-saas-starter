import type { NextRequest } from 'next/server';

import { API_BASE_URL } from '@/lib/config';
import { getAccessTokenFromCookies, getSessionMetaFromCookies } from '@/lib/auth/cookies';

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const accessToken = getAccessTokenFromCookies();
  const session = getSessionMetaFromCookies();

  if (!accessToken || !session?.tenantId) {
    return new Response('Unauthorized', { status: 401 });
  }

  const abortController = new AbortController();
  const abortListener = () => abortController.abort();
  request.signal.addEventListener('abort', abortListener);

  try {
    const upstream = await fetch(`${API_BASE_URL}/api/v1/billing/stream`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
        'X-Tenant-Id': session.tenantId,
        'X-Tenant-Role': request.headers.get('x-tenant-role') ?? 'owner',
      },
      cache: 'no-store',
      signal: abortController.signal,
    });

    if (!upstream.body) {
      return new Response('Upstream stream unavailable.', {
        status: upstream.status,
        statusText: upstream.statusText,
      });
    }

    const headers = new Headers();
    headers.set('Content-Type', upstream.headers.get('Content-Type') ?? 'text/event-stream');
    headers.set('Cache-Control', 'no-cache');
    headers.set('Connection', 'keep-alive');
    headers.set('Transfer-Encoding', 'chunked');

    return new Response(upstream.body, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers,
    });
  } finally {
    request.signal.removeEventListener('abort', abortListener);
  }
}
