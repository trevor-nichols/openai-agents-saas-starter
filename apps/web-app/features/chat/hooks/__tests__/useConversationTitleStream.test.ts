import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useConversationTitleStream } from '../useConversationTitleStream';

const closeMock = vi.fn();
let lastOptions: any;

vi.mock('@/lib/streams/conversationTitle', () => ({
  openConversationTitleStream: vi.fn((options: any) => {
    lastOptions = options;
    return { close: closeMock };
  }),
}));

describe('useConversationTitleStream', () => {
  it('subscribes and accumulates title chunks until done', async () => {
    const onTitle = vi.fn();
    const onPendingStart = vi.fn();
    const onPendingResolve = vi.fn();

    const { unmount, rerender } = renderHook(
      ({ id }) => useConversationTitleStream({ conversationId: id, onTitle, onPendingStart, onPendingResolve }),
      { initialProps: { id: 'conv-1' } },
    );

    expect(onPendingStart).toHaveBeenCalledTimes(1);

    // Stream chunks
    await act(async () => {
      lastOptions.onMessage('My ');
    });

    await act(async () => {
      lastOptions.onMessage('Title');
    });

    expect(onTitle).toHaveBeenCalledWith('My');
    expect(onTitle).toHaveBeenCalledWith('My Title');

    // Done closes out pending
    await act(async () => {
      lastOptions.onMessage('[DONE]');
    });
    expect(onPendingResolve).toHaveBeenCalledTimes(1);
    expect(closeMock).toHaveBeenCalledTimes(1);

    // Switch conversation should resubscribe and allow new title
    rerender({ id: 'conv-2' });
    await act(async () => {
      lastOptions.onMessage('New');
    });
    expect(onTitle).toHaveBeenCalledWith('New');

    unmount();
    expect(closeMock).toHaveBeenCalledTimes(3);
    expect(onPendingResolve).toHaveBeenCalledTimes(2);
  });

  it('no-ops when conversationId is null', () => {
    const onTitle = vi.fn();
    renderHook(() => useConversationTitleStream({ conversationId: null, onTitle }));
    expect(onTitle).not.toHaveBeenCalled();
  });
});
