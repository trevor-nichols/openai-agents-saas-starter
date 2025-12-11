import type { Meta, StoryObj } from '@storybook/react';

import { Progress } from '../progress';

const meta: Meta<typeof Progress> = {
  title: 'UI/Feedback/Progress',
  component: Progress,
  tags: ['autodocs'],
  argTypes: {
    value: { control: { type: 'number', min: 0, max: 100, step: 5 } },
  },
};

export default meta;

type Story = StoryObj<typeof Progress>;

export const Determinate: Story = {
  args: {
    value: 64,
  },
};

export const InlineStack: Story = {
  render: () => (
    <div className="space-y-3">
      <div>
        <p className="text-xs text-muted-foreground mb-1">Provisioning</p>
        <Progress value={35} />
      </div>
      <div>
        <p className="text-xs text-muted-foreground mb-1">Syncing data</p>
        <Progress value={68} />
      </div>
      <div>
        <p className="text-xs text-muted-foreground mb-1">Finishing</p>
        <Progress value={92} />
      </div>
    </div>
  ),
};
