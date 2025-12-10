import type { Meta, StoryObj } from '@storybook/react';
import { AppNotificationMenu } from '../AppNotificationMenu';

const meta = {
  title: 'Shell/AppNotificationMenu',
  component: AppNotificationMenu,
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof AppNotificationMenu>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex min-h-[360px] items-center justify-center bg-background text-foreground">
      <AppNotificationMenu />
    </div>
  ),
};
