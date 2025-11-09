'use server';

import { API_BASE_URL, USE_API_MOCK } from '../config';
import { getAccessTokenFromCookies } from './cookies';

export async function authenticatedFetch(path: string, init?: RequestInit) {
  const token = getAccessTokenFromCookies();
  if (!token) {
    throw new Error('Missing access token.');
  }
  if (USE_API_MOCK) {
    return mockResponse(path);
  }
  const headers = new Headers(init?.headers ?? {});
  headers.set('Authorization', `Bearer ${token}`);
  headers.set('Content-Type', headers.get('Content-Type') ?? 'application/json');

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers,
    cache: 'no-store',
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(body || `Request failed with status ${response.status}`);
  }
  return response;
}

function mockResponse(path: string): Response {
  if (path === '/api/v1/conversations') {
    return new Response(
      JSON.stringify({
        data: [
          {
            id: 'mock-conversation',
            last_message_summary: 'Welcome to Anything Agents!',
            updated_at: new Date().toISOString(),
          },
        ],
      }),
      { status: 200 },
    );
  }
  if (path === '/api/v1/auth/me') {
    return new Response(
      JSON.stringify({
        data: {
          user_id: '99999999-8888-7777-6666-555555555555',
          email: 'mock@example.com',
        },
      }),
      { status: 200 },
    );
  }
  return new Response('{}', { status: 200 });
}
