import type { Meta, StoryObj } from '@storybook/react';
import { Bell, Settings } from 'lucide-react';

import { Button } from './button';
import { Popover, PopoverContent, PopoverTrigger } from './popover';

const meta: Meta = {
  title: 'UI/Overlays/Popover',
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className="gap-2">
          <Bell className="h-4 w-4" />
          Notifications
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-72">
        <div className="space-y-2 text-sm">
          <p className="font-medium">Recent</p>
          <div className="rounded-md border border-white/10 bg-white/5 p-3">
            Deployment finished. Latency improved to 420ms p95.
          </div>
          <div className="rounded-md border border-white/10 bg-white/5 p-3">
            Billing statement available for October.
          </div>
        </div>
      </PopoverContent>
    </Popover>
  ),
};

export const WithActions: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon">
          <Settings className="h-4 w-4" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-56">
        <div className="space-y-2 text-sm">
          <p className="font-medium">Quick actions</p>
          <ul className="space-y-1 text-muted-foreground">
            <li>Toggle maintenance mode</li>
            <li>Rotate API keys</li>
            <li>View audit log</li>
          </ul>
        </div>
      </PopoverContent>
    </Popover>
  ),
};
