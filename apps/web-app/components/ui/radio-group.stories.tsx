import type { Meta, StoryObj } from '@storybook/react';
import { RadioGroup, RadioGroupItem } from './radio-group';
import { Label } from './label';

const meta: Meta<typeof RadioGroup> = {
  title: 'UI/Inputs/RadioGroup',
  component: RadioGroup,
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
      description: 'Whether the radio group is disabled',
    },
  },
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof RadioGroup>;

export const Default: Story = {
  render: () => (
    <RadioGroup defaultValue="option1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option1" id="option1" />
        <Label htmlFor="option1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option2" id="option2" />
        <Label htmlFor="option2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option3" id="option3" />
        <Label htmlFor="option3">Option 3</Label>
      </div>
    </RadioGroup>
  ),
};

export const WithDescriptions: Story = {
  render: () => (
    <RadioGroup defaultValue="starter">
      <div className="flex items-start space-x-2">
        <RadioGroupItem value="starter" id="starter" className="mt-1" />
        <div className="grid gap-1">
          <Label htmlFor="starter">Starter</Label>
          <p className="text-xs text-muted-foreground">
            Perfect for individuals and small teams
          </p>
        </div>
      </div>
      <div className="flex items-start space-x-2">
        <RadioGroupItem value="pro" id="pro" className="mt-1" />
        <div className="grid gap-1">
          <Label htmlFor="pro">Pro</Label>
          <p className="text-xs text-muted-foreground">
            For growing teams with advanced needs
          </p>
        </div>
      </div>
      <div className="flex items-start space-x-2">
        <RadioGroupItem value="enterprise" id="enterprise" className="mt-1" />
        <div className="grid gap-1">
          <Label htmlFor="enterprise">Enterprise</Label>
          <p className="text-xs text-muted-foreground">
            Custom solutions for large organizations
          </p>
        </div>
      </div>
    </RadioGroup>
  ),
};

export const Disabled: Story = {
  render: () => (
    <RadioGroup defaultValue="option1" disabled>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option1" id="disabled1" />
        <Label htmlFor="disabled1">Option 1 (Disabled)</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option2" id="disabled2" />
        <Label htmlFor="disabled2">Option 2 (Disabled)</Label>
      </div>
    </RadioGroup>
  ),
};

export const PaymentMethod: Story = {
  render: () => (
    <div className="grid w-full max-w-md gap-2">
      <Label className="text-base font-semibold">Payment Method</Label>
      <RadioGroup defaultValue="card">
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="card" id="card" />
          <Label htmlFor="card">Credit / Debit Card</Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="paypal" id="paypal" />
          <Label htmlFor="paypal">PayPal</Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="apple" id="apple" />
          <Label htmlFor="apple">Apple Pay</Label>
        </div>
        <div className="flex items-center space-x-2">
          <RadioGroupItem value="google" id="google" />
          <Label htmlFor="google">Google Pay</Label>
        </div>
      </RadioGroup>
    </div>
  ),
};

export const NotificationSettings: Story = {
  render: () => (
    <div className="grid w-full max-w-md gap-2">
      <Label className="text-base font-semibold">Email Notifications</Label>
      <RadioGroup defaultValue="all">
        <div className="flex items-start space-x-2">
          <RadioGroupItem value="all" id="all" className="mt-1" />
          <div className="grid gap-1">
            <Label htmlFor="all">All notifications</Label>
            <p className="text-xs text-muted-foreground">
              Get notified about everything
            </p>
          </div>
        </div>
        <div className="flex items-start space-x-2">
          <RadioGroupItem value="important" id="important" className="mt-1" />
          <div className="grid gap-1">
            <Label htmlFor="important">Important only</Label>
            <p className="text-xs text-muted-foreground">
              Only critical updates and alerts
            </p>
          </div>
        </div>
        <div className="flex items-start space-x-2">
          <RadioGroupItem value="none" id="none" className="mt-1" />
          <div className="grid gap-1">
            <Label htmlFor="none">None</Label>
            <p className="text-xs text-muted-foreground">
              Turn off all email notifications
            </p>
          </div>
        </div>
      </RadioGroup>
    </div>
  ),
};
