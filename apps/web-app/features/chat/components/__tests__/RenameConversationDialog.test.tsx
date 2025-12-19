import { describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { RenameConversationDialog } from '../conversation-sidebar/RenameConversationDialog';

describe('RenameConversationDialog', () => {
  it('prefills the input when opening', async () => {
    const onOpenChange = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    const view = render(
      <RenameConversationDialog
        key="closed"
        open={false}
        conversationTitle=""
        onOpenChange={onOpenChange}
        onSubmit={onSubmit}
      />,
    );

    view.rerender(
      <RenameConversationDialog
        key="conv-1"
        open={true}
        conversationTitle="Pricing updates"
        onOpenChange={onOpenChange}
        onSubmit={onSubmit}
      />,
    );

    await waitFor(() => expect(screen.getByPlaceholderText('Conversation title')).toHaveValue('Pricing updates'));
  });

  it('resets the input between opens', async () => {
    const user = userEvent.setup();
    const onOpenChange = vi.fn();
    const onSubmit = vi.fn().mockResolvedValue(undefined);

    const view = render(
      <RenameConversationDialog
        key="conv-1"
        open={true}
        conversationTitle="First title"
        onOpenChange={onOpenChange}
        onSubmit={onSubmit}
      />,
    );

    const input = screen.getByPlaceholderText('Conversation title');
    await waitFor(() => expect(input).toHaveValue('First title'));

    await user.clear(input);
    await user.type(input, 'Custom title');
    expect(input).toHaveValue('Custom title');

    view.rerender(
      <RenameConversationDialog
        key="closed"
        open={false}
        conversationTitle=""
        onOpenChange={onOpenChange}
        onSubmit={onSubmit}
      />,
    );

    view.rerender(
      <RenameConversationDialog
        key="conv-2"
        open={true}
        conversationTitle="Second title"
        onOpenChange={onOpenChange}
        onSubmit={onSubmit}
      />,
    );

    await waitFor(() => expect(screen.getByPlaceholderText('Conversation title')).toHaveValue('Second title'));
  });
});
