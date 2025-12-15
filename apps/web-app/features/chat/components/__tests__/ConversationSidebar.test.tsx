import { describe, expect, it, beforeEach, afterEach, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ConversationSidebar } from '../conversation-sidebar';
import type { ConversationListItem } from '@/types/conversations';

// Mock IntersectionObserver globally for JSDOM
const observerInstances: MockIntersectionObserver[] = [];

class MockIntersectionObserver {
  private callback: (entries: IntersectionObserverEntry[]) => void;
  public target: Element | null = null;

  constructor(cb: (entries: IntersectionObserverEntry[]) => void) {
    this.callback = cb;
    observerInstances.push(this);
  }

  observe(target: Element) {
    this.target = target;
  }

  unobserve() {
    // no-op
  }

  disconnect() {
    // no-op
  }

  trigger(isIntersecting = true) {
    this.callback([{ isIntersecting, target: this.target as Element } as IntersectionObserverEntry]);
  }
}

(globalThis as any).IntersectionObserver = MockIntersectionObserver as unknown as typeof IntersectionObserver;

const mockUseConversationSearch = vi.fn();

vi.mock('@/lib/queries/conversations', () => ({
  useConversationSearch: (...args: unknown[]) => mockUseConversationSearch(...args),
}));

const baseConversation: ConversationListItem = {
  id: 'conv-1',
  title: 'Pricing updates',
  last_message_preview: 'Summarize billing deltas',
  updated_at: new Date().toISOString(),
};

describe('ConversationSidebar', () => {
  beforeEach(() => {
    observerInstances.splice(0, observerInstances.length);
    mockUseConversationSearch.mockReset();
    mockUseConversationSearch.mockReturnValue({
      results: [],
      isLoading: false,
      isFetchingMore: false,
      loadMore: vi.fn(),
      hasNextPage: false,
    });
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.clearAllMocks();
  });

  it('switches to the search tab when typing in the search box', async () => {
    const user = userEvent.setup();

    render(
      <ConversationSidebar
        conversationList={[baseConversation]}
        isLoadingConversations={false}
        currentConversationId={null}
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
      />,
    );

    const input = screen.getByPlaceholderText('Search chats...');
    await user.type(input, 'billing');

    const resultsTab = screen.getByRole('tab', { name: 'Results' });
    expect(resultsTab).toHaveAttribute('data-state', 'active');
  });

  it('triggers loadMore when the sentinel intersects', () => {
    const loadMore = vi.fn();

    render(
      <ConversationSidebar
        conversationList={[baseConversation]}
        isLoadingConversations={false}
        loadMoreConversations={loadMore}
        hasNextConversationPage={true}
        currentConversationId={null}
        onSelectConversation={() => {}}
        onNewConversation={() => {}}
      />,
    );

    expect(observerInstances.length).toBeGreaterThan(0);
    observerInstances[0]!.trigger(true);

    expect(loadMore).toHaveBeenCalledTimes(1);
  });
});
