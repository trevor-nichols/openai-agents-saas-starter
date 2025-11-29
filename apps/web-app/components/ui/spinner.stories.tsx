import type { Meta, StoryObj } from '@storybook/react';

import { Spinner } from './spinner';

const meta: Meta<typeof Spinner> = {
  title: 'UI/Feedback/Spinner',
  component: Spinner,
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'circle', 'pinwheel', 'circle-filled', 'ellipsis', 'ring', 'bars', 'infinite'],
    },
    size: {
      control: { type: 'number', min: 12, max: 72, step: 4 },
    },
  },
  args: {
    variant: 'default',
    size: 28,
  },
};

export default meta;

type Story = StoryObj<typeof Spinner>;

export const Playground: Story = {};

export const Gallery: Story = {
  render: () => (
    <div className="flex flex-wrap items-center gap-6">
      {(['default', 'circle', 'pinwheel', 'circle-filled', 'ellipsis', 'ring', 'bars', 'infinite'] as const).map(
        (variant) => (
          <div key={variant} className="flex flex-col items-center gap-2">
            <Spinner variant={variant} size={28} />
            <span className="text-xs capitalize text-muted-foreground">{variant}</span>
          </div>
        )
      )}
    </div>
  ),
};
