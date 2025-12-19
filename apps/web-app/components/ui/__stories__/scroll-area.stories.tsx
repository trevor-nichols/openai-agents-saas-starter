import type { Meta, StoryObj } from '@storybook/react';

import { ScrollArea } from '../scroll-area';

const meta: Meta<typeof ScrollArea> = {
  title: 'UI/Layout/ScrollArea',
  component: ScrollArea,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof ScrollArea>;

export const Default: Story = {
  render: () => (
    <ScrollArea className="h-48 w-80 rounded-md border border-white/10 bg-white/5 p-4">
      <div className="space-y-2 text-sm text-muted-foreground">
        {Array.from({ length: 16 }).map((_, i) => (
          <p key={i} className="rounded-md bg-white/5 px-3 py-2 text-foreground/80">
            Activity #{i + 1}: Workspace sync completed.
          </p>
        ))}
      </div>
    </ScrollArea>
  ),
};
