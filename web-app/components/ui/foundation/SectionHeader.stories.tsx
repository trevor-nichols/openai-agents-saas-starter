import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '@/components/ui/button';

import { SectionHeader } from './SectionHeader';

const meta: Meta<typeof SectionHeader> = {
  title: 'UI/Foundation/SectionHeader',
  component: SectionHeader,
  tags: ['autodocs'],
  args: {
    title: 'Usage',
    description: 'Track your API consumption across tenants.',
    eyebrow: 'Telemetry',
  },
};

export default meta;

type Story = StoryObj<typeof SectionHeader>;

export const Default: Story = {};

export const WithActions: Story = {
  args: {
    actions: (
      <div className="flex gap-2">
        <Button variant="outline" size="sm">
          Export CSV
        </Button>
        <Button size="sm">Manage Plan</Button>
      </div>
    ),
  },
};

export const Compact: Story = {
  args: {
    size: 'compact',
    description: 'Concise header for dense layouts.',
  },
};
