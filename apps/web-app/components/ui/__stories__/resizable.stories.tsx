import type { Meta, StoryObj } from '@storybook/react';

import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '../resizable';

const meta: Meta = {
  title: 'UI/Layout/Resizable',
  parameters: {
    layout: 'padded',
  },
};

export default meta;

type Story = StoryObj<typeof meta>;

export const Horizontal: Story = {
  render: () => (
    <div className="h-64 rounded-lg border border-white/10">
      <ResizablePanelGroup direction="horizontal">
        <ResizablePanel defaultSize={45} className="p-4">
          <p className="text-sm font-medium">Left panel</p>
          <p className="text-xs text-muted-foreground mt-1">Use for navigation or filters.</p>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={55} className="p-4">
          <p className="text-sm font-medium">Right panel</p>
          <p className="text-xs text-muted-foreground mt-1">Primary content lives here.</p>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  ),
};

export const Vertical: Story = {
  render: () => (
    <div className="h-72 rounded-lg border border-white/10">
      <ResizablePanelGroup direction="vertical">
        <ResizablePanel defaultSize={60} className="p-4">
          <p className="text-sm font-medium">Top panel</p>
          <p className="text-xs text-muted-foreground mt-1">Stream logs or summary.</p>
        </ResizablePanel>
        <ResizableHandle withHandle />
        <ResizablePanel defaultSize={40} className="p-4">
          <p className="text-sm font-medium">Bottom panel</p>
          <p className="text-xs text-muted-foreground mt-1">Console or details.</p>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  ),
};
