import type { Meta, StoryObj } from '@storybook/react';

import { SubmissionSuccess } from '../components/SubmissionSuccess';

const meta: Meta<typeof SubmissionSuccess> = {
  title: 'Marketing/Access Request/Submission Success',
  component: SubmissionSuccess,
};

export default meta;

type Story = StoryObj<typeof SubmissionSuccess>;

export const InviteOnly: Story = {
  args: {
    submission: {
      email: 'security@example.com',
      organization: 'Security Labs',
      policy: 'invite_only',
    },
  },
};

export const Approval: Story = {
  args: {
    submission: {
      email: 'ops@example.com',
      organization: 'Ops Team',
      policy: 'approval',
    },
  },
};

export const Public: Story = {
  args: {
    submission: {
      email: 'admin@example.com',
      organization: 'Admin',
      policy: 'public',
    },
  },
};
