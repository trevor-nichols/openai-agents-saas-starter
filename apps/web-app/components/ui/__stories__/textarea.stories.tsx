import type { Meta, StoryObj } from '@storybook/react';
import { Textarea } from '../textarea';
import { Label } from '../label';

const meta: Meta<typeof Textarea> = {
  title: 'UI/Inputs/Textarea',
  component: Textarea,
  tags: ['autodocs'],
  argTypes: {
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the textarea is disabled',
    },
  },
  parameters: {
    layout: 'centered',
  },
};

export default meta;
type Story = StoryObj<typeof Textarea>;

export const Default: Story = {
  args: {
    placeholder: 'Type your message here...',
  },
};

export const WithValue: Story = {
  args: {
    defaultValue: 'This is some sample text that shows how the textarea looks with content.',
  },
};

export const Disabled: Story = {
  args: {
    placeholder: 'This textarea is disabled',
    disabled: true,
  },
};

export const WithLabel: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="message">Message</Label>
      <Textarea id="message" placeholder="Type your message here..." />
    </div>
  ),
};

export const WithHelperText: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="bio">Bio</Label>
      <Textarea id="bio" placeholder="Tell us about yourself..." />
      <p className="text-xs text-muted-foreground">
        Maximum 500 characters
      </p>
    </div>
  ),
};

export const MinHeight: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="small">Small Textarea</Label>
      <Textarea
        id="small"
        placeholder="Compact textarea..."
        className="min-h-[60px]"
      />
    </div>
  ),
};

export const LargeTextarea: Story = {
  render: () => (
    <div className="grid w-full max-w-md items-center gap-1.5">
      <Label htmlFor="large">Large Textarea</Label>
      <Textarea
        id="large"
        placeholder="Write a detailed description..."
        className="min-h-[200px]"
      />
    </div>
  ),
};

export const FeedbackForm: Story = {
  render: () => (
    <div className="grid w-full max-w-md gap-4">
      <div className="grid gap-1.5">
        <Label htmlFor="subject">Subject</Label>
        <input
          type="text"
          id="subject"
          placeholder="Brief summary"
          className="flex h-10 w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm"
        />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="feedback">
          Feedback <span className="text-destructive">*</span>
        </Label>
        <Textarea
          id="feedback"
          placeholder="Share your thoughts..."
          className="min-h-[120px]"
        />
        <p className="text-xs text-muted-foreground">
          Your feedback helps us improve our product
        </p>
      </div>
    </div>
  ),
};

export const WithCharacterCount: Story = {
  render: () => {
    const maxLength = 280;
    return (
      <div className="grid w-full max-w-md items-center gap-1.5">
        <Label htmlFor="tweet">Tweet</Label>
        <Textarea
          id="tweet"
          placeholder="What's happening?"
          maxLength={maxLength}
          className="min-h-[100px]"
        />
        <p className="text-xs text-muted-foreground text-right">
          0 / {maxLength}
        </p>
      </div>
    );
  },
};
