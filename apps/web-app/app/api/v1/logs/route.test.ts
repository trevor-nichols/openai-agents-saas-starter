import { vi } from 'vitest';

import { POST } from './route';

const mockFetch = vi.fn();

vi.stubGlobal('fetch', mockFetch);

describe('/api/logs proxy route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('forwards payload to backend and returns upstream body/status', async () => {
    const backendResponse = new Response(JSON.stringify({ accepted: true }), { status: 202 });
    mockFetch.mockResolvedValueOnce(backendResponse);

    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers({
        cookie: 'aa_access_token=abc',
      }),
    } as never;

    const response = await POST(request);

    expect(mockFetch).toHaveBeenCalledTimes(1);
    const call = mockFetch.mock.calls[0];
    expect(call).toBeDefined();
    const [url, options] = call as [string, RequestInit];
    expect(url).toContain('/api/v1/logs');
    expect((options as RequestInit).method).toBe('POST');
    expect((options as RequestInit).headers).toMatchObject({
      Authorization: 'Bearer abc',
    });

    expect(response.status).toBe(202);
    await expect(response.json()).resolves.toEqual({ accepted: true });
  });

  it('forwards retry-after header from upstream', async () => {
    const backendResponse = new Response(JSON.stringify({ detail: 'Rate limited' }), {
      status: 429,
      headers: { 'Retry-After': '7' },
    });
    mockFetch.mockResolvedValueOnce(backendResponse);

    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers(),
    } as never;

    const response = await POST(request);

    expect(response.status).toBe(429);
    expect(response.headers.get('Retry-After')).toBe('7');
  });

  it('returns 502 on upstream failure', async () => {
    mockFetch.mockRejectedValueOnce(new Error('boom'));
    const request = {
      json: vi.fn().mockResolvedValue({ event: 'ui.click' }),
      headers: new Headers(),
    } as never;

    const response = await POST(request);

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'boom',
    });
  });
});
