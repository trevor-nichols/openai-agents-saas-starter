import type { Meta, StoryObj } from '@storybook/react';

import { AppUserMenu } from '../AppUserMenu';
import { shellUser } from './fixtures';

const meta = {
  title: 'Shell/AppUserMenu',
  component: AppUserMenu,
  args: {
    userName: shellUser.name,
    userEmail: shellUser.email,
    tenantId: shellUser.tenantId,
    avatarUrl: shellUser.avatarUrl,
  },
} satisfies Meta<typeof AppUserMenu>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: (args) => (
    <div className="flex min-h-[320px] items-center justify-center bg-background text-foreground">
      <AppUserMenu {...args} />
    </div>
  ),
};
