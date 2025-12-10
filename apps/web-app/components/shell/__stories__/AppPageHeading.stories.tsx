import type { Meta, StoryObj } from '@storybook/react';
import { AppPageHeading } from '../AppPageHeading';
import { shellAccountItems, shellNavItems } from './fixtures';

const meta = {
  title: 'Shell/AppPageHeading',
  component: AppPageHeading,
  args: {
    navItems: shellNavItems,
    accountItems: shellAccountItems,
    subtitle: 'Workspace-wide navigation and breadcrumbs.',
  },
} satisfies Meta<typeof AppPageHeading>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Dashboard: Story = {
  parameters: { nextjs: { navigation: { pathname: '/dashboard' } } },
  render: (args) => {
    return (
      <div className="space-y-4 rounded-2xl border border-border bg-card p-6 text-foreground shadow-xl">
        <AppPageHeading {...args} />
      </div>
    );
  },
};

export const Billing: Story = {
  parameters: { nextjs: { navigation: { pathname: '/billing/usage' } } },
  render: (args) => {
    return (
      <div className="space-y-4 rounded-2xl border border-border bg-card p-6 text-foreground shadow-xl">
        <AppPageHeading {...args} subtitle="Usage and invoices for your tenant." />
      </div>
    );
  },
};
