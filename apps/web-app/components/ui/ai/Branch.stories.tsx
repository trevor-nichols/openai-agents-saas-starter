import type { Meta, StoryObj } from '@storybook/react';

import { Branch, BranchMessages, BranchNext, BranchPrevious, BranchSelector } from './branch';
import { Message, MessageAvatar, MessageContent } from './message';

const meta: Meta<typeof Branch> = {
  title: 'AI/Branch',
  component: Branch,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof Branch>;

export const Default: Story = {
  render: () => (
    <Branch defaultBranch={0}>
      <BranchMessages>
        <div key="v1">
          <Message from="assistant">
            <MessageAvatar src="https://avatar.vercel.sh/ai" name="AI" />
            <MessageContent>Version A: Use POST /chat/stream for lower latency.</MessageContent>
          </Message>
        </div>
        <div key="v2">
          <Message from="assistant">
            <MessageAvatar src="https://avatar.vercel.sh/ai" name="AI" />
            <MessageContent>Version B: Batch messages into a single completion for cost savings.</MessageContent>
          </Message>
        </div>
      </BranchMessages>
      <BranchSelector from="assistant">
        <BranchPrevious />
        <BranchNext />
      </BranchSelector>
    </Branch>
  ),
};
