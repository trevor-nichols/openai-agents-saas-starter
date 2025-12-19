import type { Meta, StoryObj } from '@storybook/react';
import { AppNavLinks } from '../AppNavLinks';
import { shellNavItems } from './fixtures';

const meta = {
  title: 'Shell/AppNavLinks',
  component: AppNavLinks,
  args: {
    items: shellNavItems,
  },
} satisfies Meta<typeof AppNavLinks>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Rail: Story = {
  parameters: { nextjs: { navigation: { pathname: '/chat' } } },
  render: (args) => {
    return (
      <div className="w-72 space-y-3 rounded-2xl border border-border bg-card p-4 text-foreground shadow-xl">
        <AppNavLinks {...args} variant="rail" />
      </div>
    );
  },
};

export const Mobile: Story = {
  parameters: { nextjs: { navigation: { pathname: '/settings/access' } } },
  render: (args) => {
    return (
      <div className="w-full max-w-sm space-y-3 rounded-2xl border border-border bg-card p-4 text-foreground shadow-xl">
        <AppNavLinks {...args} variant="mobile" />
      </div>
    );
  },
};
