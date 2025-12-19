import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../.storybook/StoryProviders';
import { MfaChallengeDialog } from '../MfaChallengeDialog';
import { authMfaChallenge } from './fixtures';

const meta = {
  title: 'Auth/MfaChallengeDialog',
  component: MfaChallengeDialog,
  args: {
    open: true,
    challenge: authMfaChallenge,
    onClose: () => {},
    onSuccess: () => {},
  },
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof MfaChallengeDialog>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: (args) => (
    <StoryProviders theme="dark">
      <div className="rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
        <MfaChallengeDialog {...args} />
      </div>
    </StoryProviders>
  ),
};
