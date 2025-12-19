import type { Meta, StoryObj } from '@storybook/react';
import { StoryProviders } from '../../../.storybook/StoryProviders';
import { ResetPasswordForm } from '../ResetPasswordForm';

const meta = {
  title: 'Auth/ResetPasswordForm',
  component: ResetPasswordForm,
  args: {
    token: 'reset_tok_123',
  },
  parameters: {
    layout: 'centered',
  },
} satisfies Meta<typeof ResetPasswordForm>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: (args) => (
    <StoryProviders theme="dark">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-6 text-foreground shadow-2xl">
        <ResetPasswordForm {...args} />
      </div>
    </StoryProviders>
  ),
};
