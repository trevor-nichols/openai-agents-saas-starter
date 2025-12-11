import type { Meta, StoryObj } from '@storybook/react';

import { PasswordPolicyList } from '../../foundation/PasswordPolicyList';

const meta: Meta<typeof PasswordPolicyList> = {
  title: 'UI/Foundation/PasswordPolicyList',
  component: PasswordPolicyList,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof PasswordPolicyList>;

const rules = [
  'At least 12 characters',
  'One uppercase and one lowercase letter',
  'One number',
  'One special character',
  'No previously used passwords',
];

export const Default: Story = {
  args: {
    items: rules,
  },
};

export const Compact: Story = {
  args: {
    items: rules.slice(0, 3),
    className: 'p-2 text-sm',
  },
};
