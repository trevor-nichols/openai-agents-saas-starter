import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useChatController } from '@/lib/chat/useChatController';
import {
  createMutationMock,
  createQueryWrapper,
} from './testUtils';

const originalFetch = global.fetch;

vi.mock('@/lib/api/conversations', () => ({
  fetchConversationHistory: vi.fn(),
  deleteConversationById: vi.fn(),
}));

vi.mock('@/lib/queries/chat', () => ({
  useSendChatMutation: vi.fn(),
}));

const { fetchConversationHistory } = vi.mocked(
  await import('@/lib/api/conversations'),
);
const { useSendChatMutation } = vi.mocked(
  await import('@/lib/queries/chat'),
);

describe('useChatController (integration)', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
    global.fetch = originalFetch;
  });

  it('streams via fetch SSE response and updates state', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(
      createMutationMock({ mutateAsync }),
    );

    fetchConversationHistory.mockImplementation(async (conversationId: string) => ({
      conversation_id: conversationId,
      created_at: '2025-01-01T00:00:00.000Z',
      updated_at: '2025-01-01T00:00:05.000Z',
      messages: [],
    }));

    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            'data: {"kind":"raw_response","conversation_id":"conv-integration","raw_type":"response.output_text.delta","text_delta":"Integrated response","is_terminal":false}\n\n',
          ),
        );
        controller.enqueue(
          encoder.encode(
            'data: {"kind":"raw_response","conversation_id":"conv-integration","raw_type":"response.completed","text_delta":"","is_terminal":true}\n\n',
          ),
        );
        controller.close();
      },
    });

    const response = new Response(stream, {
      status: 200,
      headers: { 'Content-Type': 'text/event-stream' },
    });

    global.fetch = vi.fn().mockResolvedValue(response);

    const { Wrapper } = createQueryWrapper();
    const onConversationAdded = vi.fn();

    const { result } = renderHook(
      () =>
        useChatController({
          onConversationAdded,
        }),
      { wrapper: Wrapper },
    );

    await act(async () => {
      await result.current.sendMessage('Integration test');
    });

    expect(global.fetch).toHaveBeenCalledWith(
      '/api/chat/stream',
      expect.objectContaining({
        method: 'POST',
      }),
    );
    expect(onConversationAdded).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'conv-integration' }),
    );
    expect(mutateAsync).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-integration');
    });
    await waitFor(() => {
      expect(fetchConversationHistory).toHaveBeenCalledWith('conv-integration');
    });

    const assistantMessages = result.current.messages.filter(
      (msg) => msg.role === 'assistant',
    );
    expect(assistantMessages.at(-1)?.content).toBe('Integrated response');
  });
});
