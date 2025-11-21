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
        type: 'content' as const,
        payload: 'Streaming response',
        conversationId: 'conv-99',
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
});
