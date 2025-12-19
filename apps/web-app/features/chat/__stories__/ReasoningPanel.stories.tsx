import type { Meta, StoryObj } from '@storybook/react';

import { ReasoningPanel } from '../components/chat-interface/ReasoningPanel';

const meta: Meta<typeof ReasoningPanel> = {
  title: 'Chat/ReasoningPanel',
  component: ReasoningPanel,
};

export default meta;

type Story = StoryObj<typeof ReasoningPanel>;

export const WithReasoning: Story = {
  args: {
    reasoningText: 'Analyzing billing anomalies and correlating with agent outputs.',
    isStreaming: false,
  },
};

export const Streaming: Story = {
  args: {
    reasoningText: 'Thinking through the customer request while streaming.',
    isStreaming: true,
  },
};

export const HiddenWhenEmpty: Story = {
  args: {
    reasoningText: undefined,
    isStreaming: false,
  },
};
