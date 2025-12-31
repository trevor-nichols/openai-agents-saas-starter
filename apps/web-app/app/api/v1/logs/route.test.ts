import { describe, expect, it, vi } from 'vitest';
import { http, HttpResponse } from 'msw';

import { API_BASE_URL } from '@/lib/config';
import { server } from '@/test-utils/msw/server';

async function loadHandler() {
  vi.resetModules();
  return import('./route');
}

describe('/api/logs proxy route', () => {
  const logEndpoint = `${API_BASE_URL}/api/v1/logs`;

  it('forwards payload to backend and returns upstream body/status', async () => {
    const { POST } = await loadHandler();
    let receivedAuth: string | null = null;
    let receivedBody: unknown = null;
    server.use(
      http.post(logEndpoint, async ({ request }) => {
        receivedAuth = request.headers.get('authorization');
        receivedBody = await request.json();
        return HttpResponse.json({ accepted: true }, { status: 202 });
      }),
    );

    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers({
        cookie: 'aa_access_token=abc',
      }),
    } as never;

    const response = await POST(request);

    expect(receivedAuth).toBe('Bearer abc');
    expect(receivedBody).toEqual({ event: 'ui.click' });

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual({ accepted: true });
  });

  it('forwards retry-after header from upstream', async () => {
    const { POST } = await loadHandler();
    server.use(
      http.post(
        logEndpoint,
        () =>
          new HttpResponse(JSON.stringify({ detail: 'Rate limited' }), {
            status: 429,
            headers: { 'Retry-After': '7' },
          }),
      ),
    );

    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers(),
    } as never;

    const response = await POST(request);

    expect(response.status).toBe(429);
    expect(response.headers.get('Retry-After')).toBe('7');
  });

  it('returns 502 on upstream failure', async () => {
    const { POST } = await loadHandler();
    server.use(http.post(logEndpoint, () => HttpResponse.error()));
    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers(),
    } as never;

    const response = await POST(request);

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual(
      expect.objectContaining({
        success: false,
        error: expect.stringContaining('Failed to fetch'),
      }),
    );
  });
});
