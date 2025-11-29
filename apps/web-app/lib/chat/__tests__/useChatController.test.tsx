import { act, renderHook, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { ConversationHistory } from '@/types/conversations';
import { useChatController } from '@/lib/chat/useChatController';
import {
  createMutationMock,
  createQueryWrapper,
} from './testUtils';

vi.mock('@/lib/api/conversations', () => ({
  fetchConversationHistory: vi.fn(),
  deleteConversationById: vi.fn(),
}));

vi.mock('@/lib/api/chat', () => ({
  streamChat: vi.fn(),
}));

vi.mock('@/lib/queries/chat', () => ({
  useSendChatMutation: vi.fn(),
}));

const { fetchConversationHistory, deleteConversationById } = vi.mocked(
  await import('@/lib/api/conversations'),
);
const { streamChat } = vi.mocked(await import('@/lib/api/chat'));
const { useSendChatMutation } = vi.mocked(await import('@/lib/queries/chat'));

const makeHistory = (id: string): ConversationHistory => ({
  conversation_id: id,
  created_at: '2025-01-01T00:00:00.000Z',
  updated_at: '2025-01-01T00:00:00.000Z',
  messages: [],
});

describe('useChatController', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllMocks();
  });

  beforeEach(() => {
    fetchConversationHistory.mockImplementation(async (id: string) => makeHistory(id));
  });

  it('loads conversation history via selectConversation', async () => {
    const messages: ConversationHistory = {
      conversation_id: 'conv-1',
      created_at: '2025-01-01T00:00:00.000Z',
      updated_at: '2025-01-01T00:05:00.000Z',
      messages: [
        {
          role: 'user',
          content: 'Hello there',
          timestamp: '2025-01-01T00:00:00.000Z',
        },
      ],
    };

    fetchConversationHistory.mockResolvedValue(messages);
    useSendChatMutation.mockReturnValue(createMutationMock());

    const { Wrapper } = createQueryWrapper();

    const { result } = renderHook(() => useChatController(), {
      wrapper: Wrapper,
    });

    await act(async () => {
      await result.current.selectConversation('conv-1');
    });

    expect(fetchConversationHistory).toHaveBeenCalledWith('conv-1');
    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-1');
    });
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0]).toMatchObject({
      role: 'user',
      content: 'Hello there',
    });
  });

  it('streams message content and adds new conversation on send', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(
      createMutationMock({ mutateAsync }),
    );

    streamChat.mockImplementation(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'raw_response',
          conversation_id: 'conv-99',
          agent_used: 'triage',
          response_id: 'resp-1',
          sequence_number: 1,
          raw_type: 'response.output_text.delta',
          run_item_name: null,
          run_item_type: null,
          tool_call_id: null,
          tool_name: null,
          agent: 'triage',
          new_agent: null,
          text_delta: 'Streaming response',
          reasoning_delta: null,
          is_terminal: true,
          payload: {},
        },
      };
    })());

    const onConversationAdded = vi.fn();
    const { Wrapper } = createQueryWrapper();

    const { result } = renderHook(
      () =>
        useChatController({
          onConversationAdded,
        }),
      { wrapper: Wrapper },
    );

    await act(async () => {
      await result.current.sendMessage('Tell me something');
    });

    expect(onConversationAdded).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'conv-99' }),
    );
    expect(mutateAsync).not.toHaveBeenCalled();

    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-99');
    });
    const assistantMessages = result.current.messages.filter(
      (msg) => msg.role === 'assistant',
    );
    expect(assistantMessages.at(-1)?.content).toBe('Streaming response');
  });

  it('falls back to mutation when streaming fails', async () => {
    const fallbackResponse = {
      conversation_id: 'conv-fallback',
      response: 'Fallback answered',
    };

    const mutateAsync = vi.fn().mockResolvedValue(fallbackResponse);
    useSendChatMutation.mockReturnValue(
      createMutationMock({ mutateAsync }),
    );

    streamChat.mockImplementation(() => {
      throw new Error('stream failed');
    });

    const { Wrapper } = createQueryWrapper();

    const { result } = renderHook(() => useChatController(), {
      wrapper: Wrapper,
    });

    await act(async () => {
      await result.current.sendMessage('Trigger fallback');
    });

    expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({
        message: 'Trigger fallback',
      }),
    );
    await waitFor(() => {
      expect(result.current.currentConversationId).toBe('conv-fallback');
    });
    const assistantMessages = result.current.messages.filter(
      (msg) => msg.role === 'assistant',
    );
    expect(assistantMessages.at(-1)?.content).toBe('Fallback answered');
    expect(result.current.errorMessage).toBeNull();
  });

  it('deletes conversation and resets state', async () => {
    fetchConversationHistory.mockResolvedValue({
      conversation_id: 'conv-delete',
      created_at: '2025-01-01T00:00:00.000Z',
      updated_at: '2025-01-01T00:00:00.000Z',
      messages: [],
    });
    deleteConversationById.mockResolvedValue(undefined);
    useSendChatMutation.mockReturnValue(createMutationMock());

    const reloadConversations = vi.fn();
    const onConversationRemoved = vi.fn();
    const { Wrapper } = createQueryWrapper();

    const { result } = renderHook(
      () =>
        useChatController({
          onConversationRemoved,
          reloadConversations,
        }),
      { wrapper: Wrapper },
    );

    await act(async () => {
      await result.current.selectConversation('conv-delete');
    });

    await act(async () => {
      await result.current.deleteConversation('conv-delete');
    });

    expect(deleteConversationById).toHaveBeenCalledWith('conv-delete');
    expect(onConversationRemoved).toHaveBeenCalledWith('conv-delete');
    expect(reloadConversations).toHaveBeenCalled();
    expect(result.current.currentConversationId).toBeNull();
    expect(result.current.messages).toHaveLength(0);
  });

  it('resets activeAgent to selectedAgent on new conversation after handoff', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(createMutationMock({ mutateAsync }));

    streamChat.mockImplementation(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'agent_update',
          conversation_id: 'conv-handoff',
          new_agent: 'other-agent',
          agent_used: 'other-agent',
          response_id: 'resp-2',
          sequence_number: 5,
          raw_type: null,
          run_item_name: null,
          run_item_type: null,
          tool_call_id: null,
          tool_name: null,
          agent: 'other-agent',
          text_delta: null,
          reasoning_delta: null,
          is_terminal: true,
          payload: {},
        },
      };
    })());

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('trigger handoff');
    });

    expect(result.current.activeAgent).toBe('other-agent');

    await act(async () => {
      result.current.startNewConversation();
    });

    expect(result.current.activeAgent).toBe('triage');
  });

  it('clears reasoning text between sends', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(createMutationMock({ mutateAsync }));

    // First stream provides reasoning delta
    streamChat.mockImplementationOnce(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'raw_response',
          conversation_id: 'conv-1',
          agent_used: 'triage',
          response_id: 'resp-1',
          sequence_number: 1,
          raw_type: 'response.reasoning_text.delta',
          run_item_name: null,
          run_item_type: null,
          tool_call_id: null,
          tool_name: null,
          agent: 'triage',
          new_agent: null,
          text_delta: null,
          reasoning_delta: 'thoughts',
          is_terminal: true,
          payload: {},
        },
      };
    })());

    // Second stream has no reasoning
    streamChat.mockImplementationOnce(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'raw_response',
          conversation_id: 'conv-1',
          agent_used: 'triage',
          response_id: 'resp-2',
          sequence_number: 1,
          raw_type: 'response.output_text.delta',
          run_item_name: null,
          run_item_type: null,
          tool_call_id: null,
          tool_name: null,
          agent: 'triage',
          new_agent: null,
          text_delta: 'hi',
          reasoning_delta: null,
          is_terminal: true,
          payload: {},
        },
      };
    })());

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('first');
    });
    expect(result.current.reasoningText).toBe('thoughts');

    await act(async () => {
      await result.current.sendMessage('second');
    });

    expect(result.current.reasoningText).toBe('');
  });

  it('clears tool events between sends', async () => {
    const mutateAsync = vi.fn();
    useSendChatMutation.mockReturnValue(createMutationMock({ mutateAsync }));

    // First stream emits a tool call/output
    streamChat.mockImplementationOnce(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'run_item',
          conversation_id: 'conv-1',
          agent_used: 'triage',
          response_id: 'resp-1',
          sequence_number: 1,
          raw_type: null,
          run_item_name: 'tool_called',
          run_item_type: 'tool_call_item',
          tool_call_id: 'call-1',
          tool_name: 'search',
          agent: 'triage',
          new_agent: null,
          text_delta: null,
          reasoning_delta: null,
          is_terminal: false,
          payload: { args: 'x' },
        },
      };
      yield {
        type: 'event' as const,
        event: {
          kind: 'run_item',
          conversation_id: 'conv-1',
          agent_used: 'triage',
          response_id: 'resp-1',
          sequence_number: 2,
          raw_type: null,
          run_item_name: 'tool_output',
          run_item_type: 'tool_call_output_item',
          tool_call_id: 'call-1',
          tool_name: 'search',
          agent: 'triage',
          new_agent: null,
          text_delta: null,
          reasoning_delta: null,
          is_terminal: true,
          payload: { output: 'result' },
        },
      };
    })());

    // Second stream has no tools
    streamChat.mockImplementationOnce(() => (async function* () {
      yield {
        type: 'event' as const,
        event: {
          kind: 'raw_response',
          conversation_id: 'conv-1',
          agent_used: 'triage',
          response_id: 'resp-2',
          sequence_number: 1,
          raw_type: 'response.output_text.delta',
          run_item_name: null,
          run_item_type: null,
          tool_call_id: null,
          tool_name: null,
          agent: 'triage',
          new_agent: null,
          text_delta: 'hello',
          reasoning_delta: null,
          is_terminal: true,
          payload: {},
        },
      };
    })());

    const { Wrapper } = createQueryWrapper();
    const { result } = renderHook(() => useChatController(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.sendMessage('first tool');
    });
    expect(result.current.toolEvents.length).toBeGreaterThan(0);

    await act(async () => {
      await result.current.sendMessage('second no tool');
    });

    expect(result.current.toolEvents.length).toBe(0);
  });
});
