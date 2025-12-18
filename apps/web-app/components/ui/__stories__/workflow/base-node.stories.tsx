import type { Meta, StoryObj } from '@storybook/react';

import { Badge } from '../../badge';
import {
  BaseNode,
  BaseNodeContent,
  BaseNodeFooter,
  BaseNodeHeader,
  BaseNodeHeaderTitle,
} from '../../workflow';

function DemoNode() {
  return (
    <BaseNode className="w-[360px] overflow-hidden">
      <BaseNodeHeader className="px-4 py-3">
        <BaseNodeHeaderTitle className="truncate text-base" title="Research Agent">
          Research Agent
        </BaseNodeHeaderTitle>
        <Badge variant="secondary" className="shrink-0 text-xs">
          sequential
        </Badge>
      </BaseNodeHeader>
      <div className="h-px w-full bg-border/60" />
      <BaseNodeContent className="gap-2 px-4 py-5">
        <div className="text-3xl font-semibold tracking-tight text-foreground">Running…</div>
        <div className="text-sm text-muted-foreground">We can stream to here</div>
      </BaseNodeContent>
      <BaseNodeFooter className="flex-row items-center justify-between gap-3 px-4 py-3">
        <span className="min-w-0 truncate text-xs font-mono text-foreground/80">agent-research</span>
        <span className="min-w-0 truncate text-xs text-muted-foreground">research</span>
      </BaseNodeFooter>
    </BaseNode>
  );
}

const meta: Meta = {
  title: 'UI/Workflow/BaseNode',
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj;

export const Default: Story = {
  render: () => <DemoNode />,
};

export const Selected: Story = {
  render: () => (
    <div className="react-flow__node selected">
      <DemoNode />
    </div>
  ),
};

