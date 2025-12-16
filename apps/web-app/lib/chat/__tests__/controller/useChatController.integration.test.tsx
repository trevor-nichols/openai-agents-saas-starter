import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { useChatController } from '@/lib/chat';
import {
  createMutationMock,
  createQueryWrapper,
} from '../testUtils';
import { apiV1Path } from '@/lib/apiPaths';

const originalFetch = global.fetch;

vi.mock('@/lib/api/conversations', () => ({
  fetchConversationMessages: vi.fn(),
  fetchConversationEvents: vi.fn(),
  deleteConversationById: vi.fn(),
}));

vi.mock('@/lib/queries/chat', () => ({
  useSendChatMutation: vi.fn(),
}));

const { fetchConversationEvents, fetchConversationMessages } = vi.mocked(
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

    fetchConversationEvents.mockImplementation(async ({ conversationId }: { conversationId: string }) => ({
      conversation_id: conversationId,
      items: [],
    }));
    fetchConversationMessages.mockResolvedValue({
      items: [],
      next_cursor: null,
      prev_cursor: null,
    });

    const encoder = new TextEncoder();
    const stream = new ReadableStream<Uint8Array>({
      start(controller) {
        controller.enqueue(
          encoder.encode(
            'data: {"schema":"public_sse_v1","event_id":1,"stream_id":"stream-integration","server_timestamp":"2025-12-15T00:00:00.000Z","kind":"message.delta","conversation_id":"conv-integration","response_id":"resp-integration","agent":"triage","message_id":"msg-1","delta":"Integrated response"}\n\n',
          ),
        );
        controller.enqueue(
          encoder.encode(
            'data: {"schema":"public_sse_v1","event_id":2,"stream_id":"stream-integration","server_timestamp":"2025-12-15T00:00:00.100Z","kind":"final","conversation_id":"conv-integration","response_id":"resp-integration","agent":"triage","final":{"status":"completed","response_text":"Integrated response","structured_output":null,"reasoning_summary_text":null,"refusal_text":null,"attachments":[],"usage":{"input_tokens":1,"output_tokens":1,"total_tokens":2}}}\n\n',
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
      apiV1Path('/chat/stream'),
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
      expect(fetchConversationEvents).toHaveBeenCalledWith({ conversationId: 'conv-integration' });
    });

    const assistantMessages = result.current.messages.filter(
      (msg) => msg.role === 'assistant',
    );
    expect(assistantMessages.at(-1)?.content).toBe('Integrated response');
  });
});
