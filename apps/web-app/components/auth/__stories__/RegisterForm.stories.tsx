import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../.storybook/StoryProviders';
import { RegisterForm } from '../RegisterForm';
import { authPolicyInviteOnly, authPolicyPublic } from './fixtures';

const meta = {
  title: 'Auth/RegisterForm',
  component: RegisterForm,
  args: {
    requestAccessHref: '/request-access',
  },
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof RegisterForm>;

export default meta;

type Story = StoryObj<typeof meta>;

export const PublicSignup: Story = {
  render: (args) => (
    <StoryProviders theme="dark">
      <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
        <RegisterForm {...args} policy={authPolicyPublic} />
      </div>
    </StoryProviders>
  ),
};

export const InviteOnly: Story = {
  render: (args) => (
    <StoryProviders theme="dark">
      <div className="w-full max-w-xl rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
        <RegisterForm {...args} policy={authPolicyInviteOnly} />
      </div>
    </StoryProviders>
  ),
};
