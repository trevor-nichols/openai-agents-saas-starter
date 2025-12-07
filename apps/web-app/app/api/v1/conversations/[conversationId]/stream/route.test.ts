import { vi } from 'vitest';

import type { NextRequest } from 'next/server';

import { GET } from './route';

const openConversationMetadataStream = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/conversations', () => ({
  openConversationMetadataStream,
}));

const context = (conversationId?: string): Parameters<typeof GET>[1] => ({
  params: Promise.resolve({ conversationId }),
});

describe('/api/conversations/[conversationId]/stream route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns the upstream stream response on success', async () => {
    const upstream = new Response('stream', { status: 200 });
    openConversationMetadataStream.mockResolvedValueOnce(upstream);

    const request = {
      url: 'https://example.com/api',
      signal: AbortSignal.timeout(1000),
      headers: new Headers({ 'x-tenant-role': 'admin' }),
    } as unknown as NextRequest;

    const response = await GET(request, context('conv-1'));

    expect(response.status).toBe(200);
    await expect(response.text()).resolves.toBe('stream');
    expect(openConversationMetadataStream).toHaveBeenCalledWith({
      conversationId: 'conv-1',
      signal: request.signal,
      tenantRole: 'admin',
    });
  });

  it('returns 400 when conversation id is missing', async () => {
    const request = { url: 'https://example.com/api' } as unknown as NextRequest;
    const response = await GET(request, context());

    expect(response.status).toBe(400);
    await expect(response.json()).resolves.toEqual({
      success: false,
      error: 'Conversation id is required.',
    });
    expect(openConversationMetadataStream).not.toHaveBeenCalled();
  });

  it('maps missing access token errors to 401', async () => {
    openConversationMetadataStream.mockRejectedValueOnce(new Error('Missing access token'));

    const request = {
      url: 'https://example.com/api',
      signal: AbortSignal.timeout(1000),
      headers: new Headers(),
    } as unknown as NextRequest;
    const response = await GET(request, context('conv-2'));

    const body = await response.text();
    expect(
      { status: response.status, body, calls: openConversationMetadataStream.mock.calls.length },
    ).toEqual({ status: 401, body: 'Missing access token', calls: 1 });
  });

  it('maps generic errors to 502', async () => {
    openConversationMetadataStream.mockRejectedValueOnce(new Error('boom'));

    const request = { url: 'https://example.com/api', signal: AbortSignal.timeout(1000) } as unknown as NextRequest;
    const response = await GET(request, context('conv-3'));

    expect(response.status).toBe(502);
  });
});
