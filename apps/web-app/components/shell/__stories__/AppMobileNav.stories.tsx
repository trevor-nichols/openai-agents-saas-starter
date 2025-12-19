import type { Meta, StoryObj } from '@storybook/react';
import { AppMobileNav } from '../AppMobileNav';
import { shellAccountItems, shellNavItems } from './fixtures';

const meta = {
  title: 'Shell/AppMobileNav',
  component: AppMobileNav,
  args: {
    navItems: shellNavItems,
    accountItems: shellAccountItems,
  },
} satisfies Meta<typeof AppMobileNav>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  parameters: { nextjs: { navigation: { pathname: '/dashboard' } } },
  render: (args) => {
    return (
      <div className="flex min-h-[520px] items-center justify-center bg-background text-foreground">
        <AppMobileNav {...args} />
      </div>
    );
  },
};
