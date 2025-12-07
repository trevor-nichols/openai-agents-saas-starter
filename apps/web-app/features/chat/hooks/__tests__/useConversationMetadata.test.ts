import { act, renderHook } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { useConversationMetadata } from '../useConversationMetadata';

const closeMock = vi.fn();
let lastOptions: any;

vi.mock('@/lib/streams/conversationMetadata', () => ({
  openConversationMetadataStream: vi.fn((options: any) => {
    lastOptions = options;
    return { close: closeMock };
  }),
}));

describe('useConversationMetadata', () => {
  it('subscribes and invokes onTitle when display_name arrives', async () => {
    const onTitle = vi.fn();

    const { unmount, rerender } = renderHook(
      ({ id }) => useConversationMetadata({ conversationId: id, onTitle }),
      { initialProps: { id: 'conv-1' } },
    );

    // Fire an event
    await act(async () => {
      lastOptions.onEvent({ data: { display_name: 'My Title' } });
    });

    expect(onTitle).toHaveBeenCalledWith('My Title');

    // Ignore duplicate titles
    await act(async () => {
      lastOptions.onEvent({ data: { display_name: 'My Title' } });
    });
    expect(onTitle).toHaveBeenCalledTimes(1);

    // Switch conversation should resubscribe and allow new title
    rerender({ id: 'conv-2' });
    await act(async () => {
      lastOptions.onEvent({ data: { display_name: 'New Title' } });
    });
    expect(onTitle).toHaveBeenCalledWith('New Title');

    unmount();
    expect(closeMock).toHaveBeenCalled();
  });

  it('no-ops when conversationId is null', () => {
    const onTitle = vi.fn();
    renderHook(() => useConversationMetadata({ conversationId: null, onTitle }));
    expect(onTitle).not.toHaveBeenCalled();
  });
});
