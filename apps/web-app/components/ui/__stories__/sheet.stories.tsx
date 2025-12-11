import type { Meta, StoryObj } from '@storybook/react';

import { Button } from '../button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '../sheet';

const meta: Meta = {
  title: 'UI/Overlays/Sheet',
  parameters: {
    layout: 'centered',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Sheet>
      <SheetTrigger asChild>
        <Button>Open Sheet</Button>
      </SheetTrigger>
      <SheetContent side="right" className="sm:max-w-lg">
        <SheetHeader>
          <SheetTitle>Workspace settings</SheetTitle>
          <SheetDescription>Update workspace details without leaving context.</SheetDescription>
        </SheetHeader>
        <div className="mt-4 space-y-3 text-sm text-foreground/80">
          <p>• Name: Acme Support</p>
          <p>• Region: us-east-1</p>
          <p>• Alerts: Enabled for p95 latency & errors</p>
        </div>
      </SheetContent>
    </Sheet>
  ),
};
