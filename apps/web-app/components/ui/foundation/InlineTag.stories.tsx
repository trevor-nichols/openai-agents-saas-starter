import type { Meta, StoryObj } from '@storybook/react';
import { Check, ShieldAlert } from 'lucide-react';

import { InlineTag } from './InlineTag';

const meta: Meta<typeof InlineTag> = {
  title: 'UI/Foundation/InlineTag',
  component: InlineTag,
  tags: ['autodocs'],
  argTypes: {
    tone: {
      control: 'select',
      options: ['default', 'positive', 'warning'],
    },
  },
};

export default meta;

type Story = StoryObj<typeof InlineTag>;

export const Default: Story = {
  args: {
    children: 'Default',
  },
};

export const Positive: Story = {
  args: {
    tone: 'positive',
    children: 'Healthy',
    icon: <Check className="h-3 w-3" />,
  },
};

export const Warning: Story = {
  args: {
    tone: 'warning',
    children: 'Action needed',
    icon: <ShieldAlert className="h-3 w-3" />,
  },
};
