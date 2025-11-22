import type { Meta, StoryObj } from '@storybook/react';

import { KeyValueList } from './KeyValueList';

const meta: Meta<typeof KeyValueList> = {
  title: 'UI/Foundation/KeyValueList',
  component: KeyValueList,
  tags: ['autodocs'],
};

export default meta;

type Story = StoryObj<typeof KeyValueList>;

const sampleItems = [
  { label: 'Plan', value: 'Pro', hint: 'Billed monthly' },
  { label: 'Seats', value: 12, hint: '2 pending invitations' },
  { label: 'Region', value: 'us-east-1' },
  { label: 'Status', value: 'Active', hint: 'No incidents' },
];

export const SingleColumn: Story = {
  args: {
    items: sampleItems,
    columns: 1,
  },
};

export const TwoColumns: Story = {
  args: {
    items: sampleItems,
    columns: 2,
  },
};
