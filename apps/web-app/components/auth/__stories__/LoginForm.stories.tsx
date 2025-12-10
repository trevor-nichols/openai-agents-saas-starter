import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../.storybook/StoryProviders';
import { setLoginMode } from '../../../.storybook/mocks/auth-actions';
import { LoginForm } from '../LoginForm';

const meta = {
  title: 'Auth/LoginForm',
  component: LoginForm,
  args: {
    redirectTo: '/dashboard',
  },
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof LoginForm>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: (args) => {
    setLoginMode('success');
    return (
      <StoryProviders theme="dark">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
          <LoginForm {...args} />
        </div>
      </StoryProviders>
    );
  },
};

export const MfaRequired: Story = {
  render: (args) => {
    setLoginMode('mfa');
    return (
      <StoryProviders theme="dark">
        <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
          <LoginForm {...args} />
        </div>
      </StoryProviders>
    );
  },
};
