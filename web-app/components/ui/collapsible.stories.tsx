import type { Meta, StoryObj } from '@storybook/react';
import { useState } from 'react';
import { ChevronDown, ChevronRight } from 'lucide-react';

import { Button } from './button';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from './collapsible';

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
    <Collapsible open={open} onOpenChange={setOpen} className="w-full max-w-xl rounded-lg border border-white/10 p-3">
      <div className="flex items-center justify-between gap-2">
        <div>
          <p className="text-sm font-semibold">API Keys</p>
          <p className="text-xs text-muted-foreground">Rotate keys regularly and scope permissions tightly.</p>
        </div>
        <CollapsibleTrigger asChild>
          <Button variant="ghost" size="icon" aria-label="Toggle section">
            {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent className="space-y-2 pt-3 text-sm text-foreground/80">
        <div className="rounded-md border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs">sk-live-****************</div>
        <p>Use environment-scoped keys for staging and production. Rotate on incident or quarterly cadence.</p>
      </CollapsibleContent>
    </Collapsible>
  );
};

export const Default: Story = {
  render: () => <DefaultComponent />,
};
