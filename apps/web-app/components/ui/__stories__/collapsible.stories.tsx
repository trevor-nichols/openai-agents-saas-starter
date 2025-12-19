import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { Button } from '../button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '../collapsible';

const meta: Meta<typeof Collapsible> = {
  title: 'UI/Surfaces/Collapsible',
  component: Collapsible,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Collapsible>;

const DefaultComponent = () => {
  const [open, setOpen] = useState(true);
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="w-full max-w-xl overflow-hidden rounded-2xl border shadow-sm">
      <div className="flex items-center justify-between gap-4 px-5 py-4">
        <div>
          <p className="text-sm font-semibold">API Keys</p>
          <p className="text-xs text-muted-foreground">Rotate keys regularly and scope permissions tightly.</p>
        </div>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full">
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent className="border-t bg-muted/20 px-5 py-4 text-sm text-foreground/80">
        <div className="mb-2 rounded-md border border-border bg-background px-3 py-2 font-mono text-xs">sk-live-****************</div>
        <p className="text-xs text-muted-foreground">Use environment-scoped keys for staging and production. Rotate on incident or quarterly cadence.</p>
      </CollapsibleContent>
    </Collapsible>
  );
};

export const Default: Story = {
  render: () => <DefaultComponent />,
};
