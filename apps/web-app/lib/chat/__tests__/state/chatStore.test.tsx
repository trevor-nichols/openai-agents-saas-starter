import { memo } from 'react';
import { render, screen } from '@testing-library/react';
import { vi } from 'vitest';

import { ChatControllerProvider, useChatMessages } from '../../state/chatStore';
import type { UseChatControllerReturn } from '../../controller/useChatController';
import type { ChatMessage } from '../../types';

function createController(overrides: Partial<UseChatControllerReturn> = {}): UseChatControllerReturn {
  return {
    messages: [],
    isSending: false,
    isLoadingHistory: false,
    isClearingConversation: false,
    errorMessage: null,
    historyError: null,
    currentConversationId: null,
    selectedAgent: 'triage',
    setSelectedAgent: vi.fn(),
    activeAgent: 'triage',
    agentNotices: [],
    toolEvents: [],
    toolEventAnchors: {},
    reasoningText: '',
    lifecycleStatus: 'idle',
    hasOlderMessages: false,
    isFetchingOlderMessages: false,
    loadOlderMessages: vi.fn(),
    retryMessages: vi.fn(),
    clearHistoryError: vi.fn(),
    sendMessage: vi.fn(),
    selectConversation: vi.fn(),
    startNewConversation: vi.fn(),
    deleteConversation: vi.fn(),
    clearError: vi.fn(),
    ...overrides,
  };
}

function MessageList({ onRender }: { onRender: (messages: ChatMessage[]) => void }) {
  const messages = useChatMessages();
  onRender(messages);
  return <div data-testid="count">{messages.length}</div>;
}

const MemoMessageList = memo(MessageList);

describe('chatStore selectors', () => {
  it('does not re-render consumers when unrelated state changes', () => {
    const renderSpy = vi.fn();
    const base = createController();

    const { rerender } = render(
      <ChatControllerProvider value={base}>
        <MemoMessageList onRender={renderSpy} />
      </ChatControllerProvider>,
    );

    expect(renderSpy).toHaveBeenCalledTimes(1);
    expect(screen.getByTestId('count').textContent).toBe('0');

    // change a non-message field
    rerender(
      <ChatControllerProvider value={{ ...base, errorMessage: 'oops' }}>
        <MemoMessageList onRender={renderSpy} />
      </ChatControllerProvider>,
    );

    expect(renderSpy).toHaveBeenCalledTimes(1);

    // change messages
    rerender(
      <ChatControllerProvider value={{ ...base, messages: [{ id: '1', role: 'assistant', content: 'hi' }] }}>
        <MemoMessageList onRender={renderSpy} />
      </ChatControllerProvider>,
    );

    expect(renderSpy).toHaveBeenCalledTimes(2);
    expect(screen.getByTestId('count').textContent).toBe('1');
  });
});
