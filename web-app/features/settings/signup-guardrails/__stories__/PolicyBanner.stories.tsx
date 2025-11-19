import type { Meta, StoryObj } from '@storybook/react';

import { PolicyBanner } from '../components/PolicyBanner';
import type { SignupAccessPolicy } from '@/types/signup';

const meta: Meta<typeof PolicyBanner> = {
  title: 'Settings/Signup Guardrails/Policy Banner',
  component: PolicyBanner,
};

export default meta;

type Story = StoryObj<typeof PolicyBanner>;

const policyFixture = (mode: 'public' | 'invite_only' | 'approval'): SignupAccessPolicy => ({
  policy: mode,
  invite_required: mode !== 'public',
  request_access_enabled: mode !== 'public',
});

export const InviteOnly: Story = {
  args: {
    policy: policyFixture('invite_only'),
  },
};

export const Approval: Story = {
  args: {
    policy: policyFixture('approval'),
  },
};

export const Public: Story = {
  args: {
    policy: policyFixture('public'),
  },
};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    error: 'Failed to fetch policy',
  },
};
