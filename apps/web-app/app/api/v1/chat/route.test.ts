import { vi } from 'vitest';

import type { AgentChatRequest, AgentChatResponse } from '@/lib/api/client/types.gen';
import type { NextRequest } from 'next/server';

import { POST } from './route';

const sendChatMessage = vi.hoisted(() => vi.fn());

vi.mock('@/lib/server/services/chat', () => ({
  sendChatMessage,
}));

describe('/api/chat route', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('returns the chat response on success', async () => {
    const payload: AgentChatRequest = {
      message: 'Hello',
      conversation_id: 'conv-1',
      agent_type: 'triage',
      context: null,
    };
    const agentResponse: AgentChatResponse = {
      response: 'Hi there!',
      conversation_id: 'conv-1',
      agent_used: 'triage',
      handoff_occurred: false,
      metadata: null,
      attachments: [
        {
          object_id: 'obj-1',
          filename: 'img.png',
          mime_type: 'image/png',
          size_bytes: 1024,
          url: 'https://example.com/img.png',
        },
      ],
      structured_output: { foo: 'bar' },
    };

    sendChatMessage.mockResolvedValueOnce(agentResponse);

    const request = { json: vi.fn().mockResolvedValue(payload) } as unknown as NextRequest;

    const response = await POST(request);

    expect(response.status).toBe(200);
    await expect(response.json()).resolves.toEqual(agentResponse);
    expect(sendChatMessage).toHaveBeenCalledWith(payload);
  });

  it('returns 502 when the chat service fails', async () => {
    const payload: AgentChatRequest = {
      message: 'Hello',
      conversation_id: 'conv-1',
      agent_type: 'triage',
      context: null,
    };

    sendChatMessage.mockRejectedValueOnce(new Error('boom'));

    const request = { json: vi.fn().mockResolvedValue(payload) } as unknown as NextRequest;

    const response = await POST(request);

    expect(response.status).toBe(502);
    await expect(response.json()).resolves.toEqual({ message: 'boom' });
    expect(sendChatMessage).toHaveBeenCalledWith(payload);
  });

  it('returns 401 when the chat service reports missing access token', async () => {
    const payload: AgentChatRequest = {
      message: 'Hello',
      conversation_id: 'conv-1',
      agent_type: 'triage',
      context: null,
    };

    sendChatMessage.mockRejectedValueOnce(new Error('Missing access token'));

    const request = { json: vi.fn().mockResolvedValue(payload) } as unknown as NextRequest;

    const response = await POST(request);

    expect(response.status).toBe(401);
    await expect(response.json()).resolves.toEqual({ message: 'Missing access token' });
    expect(sendChatMessage).toHaveBeenCalledWith(payload);
  });
});
