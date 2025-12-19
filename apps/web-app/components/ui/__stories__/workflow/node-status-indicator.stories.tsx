import type { Meta, StoryObj } from '@storybook/react';

import { Badge } from '../../badge';
import {
  BaseNode,
  BaseNodeContent,
  BaseNodeFooter,
  BaseNodeHeader,
  BaseNodeHeaderTitle,
  NodeStatusIndicator,
} from '../../workflow';

function DemoNode({ title }: { title: string }) {
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
        <div className="text-3xl font-semibold tracking-tight text-foreground">{title}</div>
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
  title: 'UI/Workflow/NodeStatusIndicator',
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj;

export const LoadingBorder: Story = {
  render: () => (
    <NodeStatusIndicator status="loading" variant="border">
      <DemoNode title="Running…" />
    </NodeStatusIndicator>
  ),
};

export const LoadingOverlay: Story = {
  render: () => (
    <NodeStatusIndicator status="loading" variant="overlay">
      <DemoNode title="Running…" />
    </NodeStatusIndicator>
  ),
};

export const Statuses: Story = {
  render: () => (
    <div className="grid gap-8 md:grid-cols-2">
      <NodeStatusIndicator status="initial" variant="border">
        <DemoNode title="Ready" />
      </NodeStatusIndicator>
      <NodeStatusIndicator status="loading" variant="border">
        <DemoNode title="Running…" />
      </NodeStatusIndicator>
      <NodeStatusIndicator status="success" variant="border">
        <DemoNode title="Completed" />
      </NodeStatusIndicator>
      <NodeStatusIndicator status="error" variant="border">
        <DemoNode title="Error" />
      </NodeStatusIndicator>
    </div>
  ),
};

