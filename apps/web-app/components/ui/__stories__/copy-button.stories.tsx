import type { Meta, StoryObj } from '@storybook/react';

import { CopyButton } from '../copy-button';

const meta: Meta<typeof CopyButton> = {
  title: 'UI/Feedback/CopyButton',
  component: CopyButton,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof CopyButton>;

export const Default: Story = {
  args: {
    content: 'pnpm storybook',
  },
};

export const Muted: Story = {
  args: {
    content: 'https://example.com',
    variant: 'muted',
    size: 'md',
  },
};
