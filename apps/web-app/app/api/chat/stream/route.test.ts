import { vi } from 'vitest';

import type { AgentChatRequest } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const openChatStream = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/chat', () => ({
  openChatStream,
}));

describe('/api/chat/stream route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns the upstream stream response', async () => {
    const payload: AgentChatRequest = {
      message: 'Hello',
      conversation_id: 'conv-1',
      agent_type: 'triage',
      context: null,
    };

    const upstream = new Response('stream', {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    });

    openChatStream.mockResolvedValueOnce(upstream);

    const request = {
      json: vi.fn().mockResolvedValue(payload),
      signal: new AbortController().signal,
    } as unknown as NextRequest;

    const response = await POST(request);

    expect(openChatStream).toHaveBeenCalledWith(payload, expect.any(Object));
    expect(response.status).toBe(200);
    expect(response.headers.get('Content-Type')).toBe('text/event-stream');
  });

  it('returns 401 when upstream throws missing token', async () => {
    const payload: AgentChatRequest = {
      message: 'Hello',
      conversation_id: 'conv-1',
      agent_type: 'triage',
      context: null,
    };

    openChatStream.mockRejectedValueOnce(new Error('Missing access token'));

    const request = {
      json: vi.fn().mockResolvedValue(payload),
      signal: new AbortController().signal,
    } as unknown as NextRequest;

    const response = await POST(request);

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
  });
});
