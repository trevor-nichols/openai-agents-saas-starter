import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useChatController } from '@/lib/chat';
import { createMutationMock, createQueryWrapper } from '../testUtils';

vi.mock('@/lib/api/conversations', () => ({
  fetchConversationMessages: vi.fn(),
  fetchConversationLedgerEvents: vi.fn(),
  deleteConversationById: vi.fn(),
  deleteConversationMessage: vi.fn(),
}));

vi.mock('@/lib/api/chat', () => ({
  streamChat: vi.fn(),
}));

vi.mock('@/lib/queries/chat', () => ({
  useSendChatMutation: vi.fn(),
}));

const { fetchConversationMessages, fetchConversationLedgerEvents, deleteConversationMessage } = vi.mocked(
  await import('@/lib/api/conversations'),
);
const { streamChat } = vi.mocked(await import('@/lib/api/chat'));
const { useSendChatMutation } = vi.mocked(await import('@/lib/queries/chat'));

describe('useChatController', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    fetchConversationLedgerEvents.mockResolvedValue([]);
    fetchConversationMessages.mockResolvedValue({ items: [], next_cursor: null, prev_cursor: null });
    useSendChatMutation.mockReturnValue(createMutationMock());
  });

  it('loads conversation messages via selectConversation', async () => {
    fetchConversationMessages.mockResolvedValue({
      items: [
        {
          role: 'user',
          content: 'Hello there',
          timestamp: '2025-01-01T00:00:00.000Z',
        },
      ],
      next_cursor: null,
      prev_cursor: null,
    });

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.selectConversation('conv-1');
    });

    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-1');
      expect(fetchConversationMessages).toHaveBeenCalled();
      expect(fetchConversationLedgerEvents).toHaveBeenCalledWith({ conversationId: 'conv-1' });
      expect(result.current.messages).toHaveLength(1);
    });

    expect(result.current.messages[0]).toMatchObject({
      role: 'user',
      content: 'Hello there',
    });
  });

  it('deletes a persisted user message', async () => {
    fetchConversationMessages.mockResolvedValueOnce({
      items: [
        {
          message_id: '123',
          role: 'user',
          content: 'Hello there',
          timestamp: '2025-01-01T00:00:00.000Z',
        },
      ],
      next_cursor: null,
      prev_cursor: null,
    });

    deleteConversationMessage.mockResolvedValueOnce({
      conversation_id: 'conv-1',
      deleted_message_id: '123',
    });

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.selectConversation('conv-1');
    });

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(1);
    });

    await act(async () => {
      await result.current.deleteMessage('123');
    });

    expect(deleteConversationMessage).toHaveBeenCalledWith({
      conversationId: 'conv-1',
      messageId: '123',
    });
  });

  it('surfaces errors when message fetch fails', async () => {
    fetchConversationMessages.mockRejectedValue(new Error('boom'));

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.selectConversation('conv-err');
    });

    await waitFor(() => {
      expect(result.current.historyError ?? '').toMatch(/boom/);
    });
  });

  it('streams message content and adds new conversation on send', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(createMutationMock({ mutateAsync }));

    streamChat.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 1,
            stream_id: 'stream-test',
            server_timestamp: '2025-12-15T00:00:00.000Z',
            kind: 'message.delta',
            conversation_id: 'conv-99',
            response_id: 'resp-1',
            agent: 'triage',
            output_index: 0,
            item_id: 'msg-1',
            content_index: 0,
            delta: 'Streaming response',
          },
        };
        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 2,
            stream_id: 'stream-test',
            server_timestamp: '2025-12-15T00:00:00.100Z',
            kind: 'final',
            conversation_id: 'conv-99',
            response_id: 'resp-1',
            agent: 'triage',
            final: {
              status: 'completed',
              response_text: 'Streaming response',
              structured_output: null,
              reasoning_summary_text: null,
              refusal_text: null,
              attachments: [],
              usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
            },
          },
        };
      })(),
    );

    const onConversationAdded = vi.fn();
    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController({ onConversationAdded }), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('Tell me something');
    });

    expect(onConversationAdded).toHaveBeenCalledWith(expect.objectContaining({ id: 'conv-99' }));
    expect(mutateAsync).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-99');
    });

    const assistantMessages = result.current.messages.filter((msg) => msg.role === 'assistant');
    expect(assistantMessages.at(-1)?.content).toBe('Streaming response');
  });

  it('does not append an assistant message for tool-only turns', async () => {
    streamChat.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 1,
            stream_id: 'stream-tool-only',
            server_timestamp: '2025-12-15T00:00:00.000Z',
            kind: 'tool.status',
            conversation_id: 'conv-tool-only',
            response_id: 'resp-tool',
            agent: 'triage',
            output_index: 0,
            item_id: 'tool-1',
            tool: {
              tool_type: 'web_search',
              tool_call_id: 'tool-1',
              status: 'searching',
              query: 'hello',
            },
          },
        };
        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 2,
            stream_id: 'stream-tool-only',
            server_timestamp: '2025-12-15T00:00:00.050Z',
            kind: 'final',
            conversation_id: 'conv-tool-only',
            response_id: 'resp-tool',
            agent: 'triage',
            final: {
              status: 'completed',
              response_text: null,
              structured_output: null,
              reasoning_summary_text: null,
              refusal_text: null,
              attachments: [],
              usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
            },
          },
        };
      })(),
    );

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('tool-only please');
    });

    const assistantMessages = result.current.messages.filter((msg) => msg.role === 'assistant');
    expect(assistantMessages).toHaveLength(0);
    expect(result.current.toolEvents.length).toBeGreaterThan(0);
  });

  it('anchors output-only tools under the user turn', async () => {
    streamChat.mockImplementation(() =>
      (async function* () {
        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 1,
            stream_id: 'stream-output-only',
            server_timestamp: '2025-12-15T00:00:00.000Z',
            kind: 'message.delta',
            conversation_id: 'conv-output-only',
            response_id: 'resp-output-only',
            agent: 'triage',
            output_index: 1,
            item_id: 'msg-output-only',
            content_index: 0,
            delta: 'Here is the answer.',
          },
        };

        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 2,
            stream_id: 'stream-output-only',
            server_timestamp: '2025-12-15T00:00:00.050Z',
            kind: 'tool.output',
            conversation_id: 'conv-output-only',
            response_id: 'resp-output-only',
            agent: 'triage',
            output_index: 0,
            item_id: 'call-output-only',
            tool_call_id: 'call-output-only',
            tool_type: 'function',
            output: { ok: true },
          },
        };

        yield {
          type: 'event' as const,
          event: {
            schema: 'public_sse_v1',
            event_id: 3,
            stream_id: 'stream-output-only',
            server_timestamp: '2025-12-15T00:00:00.100Z',
            kind: 'final',
            conversation_id: 'conv-output-only',
            response_id: 'resp-output-only',
            agent: 'triage',
            final: {
              status: 'completed',
              response_text: 'Here is the answer.',
              structured_output: null,
              reasoning_summary_text: null,
              refusal_text: null,
              attachments: [],
              usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
            },
          },
        };
      })(),
    );

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('Trigger output-only tool anchoring');
    });

    await waitFor(() => {
      expect(result.current.toolEvents.some((tool) => tool.id === 'call-output-only')).toBe(true);
    });

    const userMessage = result.current.messages.find((msg) => msg.role === 'user');
    const assistantMessage = result.current.messages.find((msg) => msg.role === 'assistant');
    expect(userMessage).toBeTruthy();
    expect(assistantMessage).toBeTruthy();

    expect(result.current.toolEventAnchors[userMessage!.id]).toEqual(['call-output-only']);
    expect(result.current.toolEventAnchors[assistantMessage!.id]).toBeUndefined();
  });

  it('keeps tool events anchored even when assistant messages are queued', async () => {
    const originalRaf = globalThis.requestAnimationFrame;
    const originalCancelRaf = globalThis.cancelAnimationFrame;

    try {
      const rafCallbacks: FrameRequestCallback[] = [];
      globalThis.requestAnimationFrame = ((callback: FrameRequestCallback) => {
        rafCallbacks.push(callback);
        return rafCallbacks.length;
      }) as typeof requestAnimationFrame;
      globalThis.cancelAnimationFrame = ((_) => {
        // noop for tests
      }) as typeof cancelAnimationFrame;

      const createDeferred = () => {
        let resolve!: () => void;
        const promise = new Promise<void>((res) => {
          resolve = res;
        });
        return { promise, resolve };
      };

      const pauseAfterFirstDelta = createDeferred();
      const pauseAfterTool = createDeferred();

      streamChat.mockImplementation(() =>
        (async function* () {
          yield {
            type: 'event' as const,
            event: {
              schema: 'public_sse_v1',
              event_id: 1,
              stream_id: 'stream-anchoring',
              server_timestamp: '2025-12-15T00:00:00.000Z',
              kind: 'message.delta',
              conversation_id: 'conv-anchor',
              response_id: 'resp-anchor',
              agent: 'triage',
              output_index: 1,
              item_id: 'msg-1',
              content_index: 0,
              delta: 'Let me check.',
            },
          };

          await pauseAfterFirstDelta.promise;

          yield {
            type: 'event' as const,
            event: {
              schema: 'public_sse_v1',
              event_id: 2,
              stream_id: 'stream-anchoring',
              server_timestamp: '2025-12-15T00:00:00.050Z',
              kind: 'tool.status',
              conversation_id: 'conv-anchor',
              response_id: 'resp-anchor',
              agent: 'triage',
              output_index: 0,
              item_id: 'tool-1',
              tool: {
                tool_type: 'web_search',
                tool_call_id: 'tool-1',
                status: 'searching',
                query: 'hello',
              },
            },
          };

          await pauseAfterTool.promise;

          yield {
            type: 'event' as const,
            event: {
              schema: 'public_sse_v1',
              event_id: 3,
              stream_id: 'stream-anchoring',
              server_timestamp: '2025-12-15T00:00:00.100Z',
              kind: 'final',
              conversation_id: 'conv-anchor',
              response_id: 'resp-anchor',
              agent: 'triage',
              final: {
                status: 'completed',
                response_text: 'Let me check.',
                structured_output: null,
                reasoning_summary_text: null,
                refusal_text: null,
                attachments: [],
                usage: { input_tokens: 1, output_tokens: 1, total_tokens: 2 },
              },
            },
          };
        })(),
      );

      const { Wrapper } = createQueryWrapper();
      const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

      let sendPromise: Promise<void> | null = null;
      await act(async () => {
        sendPromise = result.current.sendMessage('Trigger tool anchoring');
      });

      await waitFor(() => {
        expect(rafCallbacks.length).toBeGreaterThan(0);
      });
      expect(result.current.messages.some((msg) => msg.role === 'assistant')).toBe(false);

      await act(async () => {
        pauseAfterFirstDelta.resolve();
      });

      await waitFor(() => {
        expect(result.current.toolEvents.some((tool) => tool.id === 'tool-1')).toBe(true);
      });

      const user = result.current.messages.find((msg) => msg.role === 'user');
      expect(user).toBeTruthy();
      expect(result.current.toolEventAnchors[user!.id]).toEqual(['tool-1']);

      await act(async () => {
        pauseAfterTool.resolve();
      });
      await act(async () => {
        await sendPromise;
      });
    } finally {
      globalThis.requestAnimationFrame = originalRaf;
      globalThis.cancelAnimationFrame = originalCancelRaf;
    }
  });
});
