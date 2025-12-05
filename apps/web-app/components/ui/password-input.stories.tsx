import type { Meta, StoryObj } from '@storybook/react';
import { PasswordInput } from './password-input';
import { Label } from './label';

const meta: Meta<typeof PasswordInput> = {
  title: 'UI/Inputs/PasswordInput',
  component: PasswordInput,
  tags: ['autodocs'],
  argTypes: {
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
    },
  },
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof PasswordInput>;

export const Default: Story = {
  args: {
    placeholder: 'Enter your password',
  },
};

export const WithValue: Story = {
  args: {
    defaultValue: 'secret123',
  },
};

export const Disabled: Story = {
  args: {
    placeholder: 'Password',
    disabled: true,
  },
};

export const WithLabel: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <PasswordInput id="password" placeholder="Enter your password" />
    </div>
  ),
};

export const LoginForm: Story = {
  render: () => (
    <div className="grid w-full max-w-sm gap-4">
      <div className="grid gap-1.5">
        <Label htmlFor="email">Email</Label>
        <input
          type="email"
          id="email"
          placeholder="name@example.com"
          className="flex h-10 w-full rounded-full border border-input/50 bg-muted/50 px-4 py-2 text-base shadow-sm transition-all file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:bg-background disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
        />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="login-password">Password</Label>
        <PasswordInput id="login-password" placeholder="Enter your password" />
      </div>
    </div>
  ),
};

export const WithHelperText: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="new-password">New Password</Label>
      <PasswordInput id="new-password" placeholder="Choose a strong password" />
      <p className="text-xs text-muted-foreground">
        Must be at least 8 characters with uppercase, lowercase, and numbers
      </p>
    </div>
  ),
};
