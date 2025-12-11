import type { Meta, StoryObj } from '@storybook/react';
import { Copy, Download, Sparkles } from 'lucide-react';

import { Action, Actions } from '../../ai/actions';

const meta: Meta<typeof Actions> = {
  title: 'AI/Actions',
  component: Actions,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Actions>;

export const Default: Story = {
  render: () => (
    <Actions>
      <Action tooltip="Copy" label="Copy">
        <Copy className="h-4 w-4" />
      </Action>
      <Action tooltip="Download" label="Download">
        <Download className="h-4 w-4" />
      </Action>
      <Action tooltip="Improve" label="Improve">
        <Sparkles className="h-4 w-4" />
      </Action>
    </Actions>
  ),
};
