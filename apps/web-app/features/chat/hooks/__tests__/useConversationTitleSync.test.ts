import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import type { ConversationListItem } from '@/types/conversations';

import { useConversationTitleSync } from '../useConversationTitleSync';

let lastOptions: any;

vi.mock('../useConversationTitleStream', () => ({
  useConversationTitleStream: vi.fn((options: any) => {
    lastOptions = options;
  }),
}));

describe('useConversationTitleSync', () => {
  beforeEach(() => {
    lastOptions = null;
  });

  it('updates pending state and title via stream callbacks', async () => {
    const base: ConversationListItem = {
      id: 'conv-1',
      updated_at: '2025-01-01T00:00:00.000Z',
      topic_hint: null,
      agent_entrypoint: null,
      active_agent: null,
      status: null,
      message_count: 0,
      last_message_preview: undefined,
    };
    const currentConversation: ConversationListItem = {
      ...base,
      display_name: 'Old Title',
    };
    const updateConversationInList = vi.fn();
    const getConversationBase = vi.fn(() => base);

    renderHook(() =>
      useConversationTitleSync({
        conversationId: 'conv-1',
        currentConversation,
        updateConversationInList,
        getConversationBase,
      }),
    );

    expect(lastOptions?.conversationId).toBe('conv-1');

    await act(async () => {
      lastOptions.onPendingStart();
    });

    expect(getConversationBase).toHaveBeenCalledWith('conv-1', currentConversation);
    expect(updateConversationInList).toHaveBeenCalledWith({
      ...base,
      display_name_pending: true,
    });

    await act(async () => {
      lastOptions.onTitle('New Title');
    });

    expect(updateConversationInList).toHaveBeenCalledWith({
      ...base,
      display_name: 'New Title',
      title: 'New Title',
    });

    await act(async () => {
      lastOptions.onPendingResolve();
    });

    expect(updateConversationInList).toHaveBeenCalledWith({
      ...base,
      display_name_pending: false,
    });
  });

  it('no-ops when conversationId is null', async () => {
    const updateConversationInList = vi.fn();
    const getConversationBase = vi.fn();

    renderHook(() =>
      useConversationTitleSync({
        conversationId: null,
        currentConversation: null,
        updateConversationInList,
        getConversationBase,
      }),
    );

    await act(async () => {
      lastOptions.onPendingStart();
      lastOptions.onTitle('Ignored');
      lastOptions.onPendingResolve();
    });

    expect(getConversationBase).not.toHaveBeenCalled();
    expect(updateConversationInList).not.toHaveBeenCalled();
  });
});
