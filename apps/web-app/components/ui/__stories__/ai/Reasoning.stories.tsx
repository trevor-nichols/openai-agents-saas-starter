import type { Meta, StoryObj } from '@storybook/react';

import { Reasoning, ReasoningContent, ReasoningTrigger } from '../../ai/reasoning';

const meta: Meta<typeof Reasoning> = {
  title: 'AI/Reasoning',
  component: Reasoning,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Reasoning>;

export const Streaming: Story = {
  render: () => (
    <Reasoning isStreaming defaultOpen>
      <ReasoningTrigger />
      <ReasoningContent>
        {`Planning steps:\n1) Fetch billing events (last 24h)\n2) Aggregate by status\n3) Return CSV download link`}
      </ReasoningContent>
    </Reasoning>
  ),
};

export const Completed: Story = {
  render: () => (
    <Reasoning duration={6}>
      <ReasoningTrigger />
      <ReasoningContent>
        {`Validated Stripe signature, stored 124 events, emitted webhook receipts.`}
      </ReasoningContent>
    </Reasoning>
  ),
};
