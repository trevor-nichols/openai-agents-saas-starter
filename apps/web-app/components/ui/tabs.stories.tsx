import type { Meta, StoryObj } from '@storybook/react';

import { Tabs, TabsContent, TabsList, TabsTrigger } from './tabs';

const meta: Meta<typeof Tabs> = {
  title: 'UI/Navigation/Tabs',
  component: Tabs,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Tabs>;

export const Default: Story = {
  render: () => (
    <Tabs defaultValue="overview" className="w-full max-w-xl">
      <TabsList className="w-full justify-start">
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="usage">Usage</TabsTrigger>
        <TabsTrigger value="alerts">Alerts</TabsTrigger>
      </TabsList>
      <TabsContent value="overview" className="mt-4 text-sm text-foreground/80">
        Quick snapshot of your workspace. Latency p95: 420ms, uptime: 99.96%.
      </TabsContent>
      <TabsContent value="usage" className="mt-4 text-sm text-foreground/80">
        142k monthly queries, 12 seats. Token spend capped at $2,000.
      </TabsContent>
      <TabsContent value="alerts" className="mt-4 text-sm text-foreground/80">
        No active alerts. Configure thresholds in Settings → Notifications.
      </TabsContent>
    </Tabs>
  ),
};
