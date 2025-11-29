import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { vi } from 'vitest';

import { ConversationArchivePanel } from '../ConversationArchivePanel';
import { createQueryWrapper } from '@/lib/chat/__tests__/testUtils';

vi.mock('@/lib/api/conversations', async () => {
  const actual = await vi.importActual<typeof import('@/lib/api/conversations')>(
    '@/lib/api/conversations',
  );
  return {
    ...actual,
    searchConversations: vi.fn(),
  };
});

const { searchConversations } = vi.mocked(await import('@/lib/api/conversations'));

describe('ConversationArchivePanel', () => {
  beforeEach(() => {
    searchConversations.mockReset();
  });

  it('shows the search empty state with clear action when a query returns no matches', async () => {
    searchConversations.mockResolvedValueOnce({ items: [], next_cursor: null });
    const { Wrapper } = createQueryWrapper();

    render(
      <Wrapper>
        <ConversationArchivePanel
          conversationList={[
            {
              id: 'conv-1',
              title: 'Alpha conversation',
              last_message_summary: 'Summary',
              updated_at: '2025-01-01T00:00:00.000Z',
            },
          ]}
          isLoading={false}
          error={null}
          onRefresh={vi.fn()}
          onSelectConversation={vi.fn()}
        />
      </Wrapper>,
    );

    // Baseline: conversations render before searching.
    expect(screen.getByText(/alpha conversation/i)).toBeInTheDocument();

    // Enter a search term that yields zero matches.
    fireEvent.change(screen.getByPlaceholderText(/search by title/i), { target: { value: 'zzz' } });
    await waitFor(() => expect(screen.getByText(/no results found/i)).toBeInTheDocument());
    expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument();

    // Clearing the query restores the default view.
    fireEvent.change(screen.getByPlaceholderText(/search by title/i), { target: { value: '' } });
    await waitFor(() => expect(screen.queryByText(/no results found/i)).not.toBeInTheDocument());

    expect(screen.getByText(/alpha conversation/i)).toBeInTheDocument();
  });
});
