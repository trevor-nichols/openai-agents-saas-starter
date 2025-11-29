import type { Meta, StoryObj } from '@storybook/react';
import { Plus } from 'lucide-react';

import { Button } from './button';
import { NavBar, type NavBarNavItem } from './nav-bar';

const meta: Meta<typeof NavBar> = {
  title: 'UI/Navigation/NavBar',
  component: NavBar,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof NavBar>;

const links: NavBarNavItem[] = [
  { href: '#dashboard', label: 'Dashboard' },
  { href: '#agents', label: 'Agents' },
  { href: '#billing', label: 'Billing' },
  { href: '#status', label: 'Status' },
];

export const Default: Story = {
  args: {
    navigationLinks: links,
    notificationCount: 2,
  },
};

export const WithCustomAction: Story = {
  args: {
    navigationLinks: links,
    actions: (
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          Changelog
        </Button>
        <Button size="sm">
          <Plus className="h-4 w-4" />
          New agent
        </Button>
      </div>
    ),
  },
};
