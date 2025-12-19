import type { Meta, StoryObj } from '@storybook/react';
import { AppSidebar } from '../AppSidebar';
import { SidebarProvider } from '../../ui/sidebar';
import { shellAccountItems, shellNavItems, shellUser } from './fixtures';

const meta = {
  title: 'Shell/AppSidebar',
  component: AppSidebar,
  args: {
    navItems: shellNavItems,
    accountItems: shellAccountItems,
    user: shellUser,
    brandLabel: 'Acme AI',
    brandHref: '/dashboard',
  },
  parameters: {
    layout: 'fullscreen',
  },
} satisfies Meta<typeof AppSidebar>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  parameters: { nextjs: { navigation: { pathname: '/dashboard' } } },
  render: (args) => {
    return (
      <SidebarProvider defaultOpen>
        <div className="flex min-h-[720px] bg-background text-foreground">
          <AppSidebar {...args} />
          <div className="flex-1 bg-gradient-to-br from-background via-muted/40 to-background" />
        </div>
      </SidebarProvider>
    );
  },
};

export const BillingActive: Story = {
  parameters: { nextjs: { navigation: { pathname: '/billing/usage' } } },
  render: (args) => {
    return (
      <SidebarProvider defaultOpen>
        <div className="flex min-h-[720px] bg-background text-foreground">
          <AppSidebar {...args} />
          <div className="flex-1 bg-gradient-to-br from-background via-muted/40 to-background" />
        </div>
      </SidebarProvider>
    );
  },
};
