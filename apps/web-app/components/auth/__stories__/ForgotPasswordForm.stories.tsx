import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../.storybook/StoryProviders';
import { ForgotPasswordForm } from '../ForgotPasswordForm';

const meta = {
  title: 'Auth/ForgotPasswordForm',
  component: ForgotPasswordForm,
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof ForgotPasswordForm>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <StoryProviders theme="dark">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
        <ForgotPasswordForm />
      </div>
    </StoryProviders>
  ),
};
