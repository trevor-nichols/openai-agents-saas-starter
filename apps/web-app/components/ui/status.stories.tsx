import type { Meta, StoryObj } from '@storybook/react';

import { Status, StatusIndicator, StatusLabel } from './status';

const meta: Meta<typeof Status> = {
  title: 'UI/Feedback/Status',
  component: Status,
  tags: ['autodocs'],
  argTypes: {
    status: {
      control: 'select',
      options: ['online', 'offline', 'maintenance', 'degraded'],
    },
  },
  args: {
    status: 'online',
  },
};

export default meta;

type Story = StoryObj<typeof Status>;

export const Default: Story = {
  args: {
    children: (
      <>
        <StatusIndicator />
        <StatusLabel />
      </>
    ),
  },
};

export const InlineLegend: Story = {
  render: () => (
    <div className="flex flex-wrap gap-3">
      {(['online', 'maintenance', 'degraded', 'offline'] as const).map((status) => (
        <Status key={status} status={status}>
          <StatusIndicator />
          <StatusLabel />
        </Status>
      ))}
    </div>
  ),
};
