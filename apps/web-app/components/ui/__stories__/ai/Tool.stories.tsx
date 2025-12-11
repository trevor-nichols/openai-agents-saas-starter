import type { Meta, StoryObj } from '@storybook/react';

import { Tool, ToolContent, ToolHeader, ToolInput, ToolOutput } from '../../ai/tool';

const meta: Meta<typeof Tool> = {
  title: 'AI/Tool',
  component: Tool,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Tool>;

const sampleInput = { action: 'fetch_usage', tenant: 'acme', period: '24h' };

export const Running: Story = {
  render: () => (
    <Tool defaultOpen>
      <ToolHeader type="tool-usage.fetch" state="input-available" />
      <ToolContent>
        <ToolInput input={sampleInput} />
      </ToolContent>
    </Tool>
  ),
};

export const Completed: Story = {
  render: () => (
    <Tool defaultOpen>
      <ToolHeader type="tool-usage.fetch" state="output-available" />
      <ToolContent>
        <ToolInput input={sampleInput} />
        <ToolOutput output={<pre className="p-3">{"{\"count\":124,\"p95\":420}"}</pre>} errorText={undefined} />
      </ToolContent>
    </Tool>
  ),
};

export const ErrorState: Story = {
  render: () => (
    <Tool defaultOpen>
      <ToolHeader type="tool-billing.sync" state="output-error" />
      <ToolContent>
        <ToolInput input={{ action: 'sync' }} />
        <ToolOutput output={null} errorText="Stripe signature invalid" />
      </ToolContent>
    </Tool>
  ),
};
