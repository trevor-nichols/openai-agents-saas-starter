import { NextResponse } from 'next/server';

import { API_BASE_URL } from '@/lib/config';
import { getAccessTokenFromCookies } from '@/lib/auth/cookies';

type RouteParams = { params: Promise<{ fileId: string }> };

export async function GET(_request: Request, { params }: RouteParams) {
  const token = await getAccessTokenFromCookies();
  if (!token) {
    return NextResponse.json({ message: 'Missing access token.' }, { status: 401 });
  }

  const { fileId } = await params;
  if (!fileId) {
    return NextResponse.json({ message: 'fileId is required.' }, { status: 400 });
  }

  const baseUrl = API_BASE_URL.endsWith('/') ? API_BASE_URL.slice(0, -1) : API_BASE_URL;

  const upstream = await fetch(`${baseUrl}/api/v1/openai/files/${fileId}/download`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!upstream.ok || !upstream.body) {
    const message = `Failed to download file (${upstream.status})`;
    return NextResponse.json({ message }, { status: upstream.status || 502 });
  }

  // Stream through with original headers
  const headers = new Headers();
  const contentType = upstream.headers.get('content-type');
  const disposition = upstream.headers.get('content-disposition');
  if (contentType) headers.set('content-type', contentType);
  if (disposition) headers.set('content-disposition', disposition);
  const cacheControl = upstream.headers.get('cache-control');
  if (cacheControl) headers.set('cache-control', cacheControl);

  return new NextResponse(upstream.body, {
    status: upstream.status,
    headers,
  });
}
