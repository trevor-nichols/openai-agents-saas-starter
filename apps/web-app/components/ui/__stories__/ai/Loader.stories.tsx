import type { Meta, StoryObj } from '@storybook/react';

import { Loader } from '../../ai/loader';

const meta: Meta<typeof Loader> = {
  title: 'AI/Loader',
  component: Loader,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Loader>;

export const Small: Story = {
  args: {
    size: 16,
  },
};

export const Large: Story = {
  args: {
    size: 32,
  },
};
