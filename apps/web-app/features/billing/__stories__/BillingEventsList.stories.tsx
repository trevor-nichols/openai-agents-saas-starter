'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { BillingEventsList } from '../components/BillingEventsList';
import { mockBillingEvents } from './fixtures';

const meta: Meta<typeof BillingEventsList> = {
  title: 'Billing/BillingEventsList',
  component: BillingEventsList,
  args: {
    events: mockBillingEvents,
    streamStatus: 'open',
  },
};

export default meta;

type Story = StoryObj<typeof BillingEventsList>;

export const Default: Story = {};

export const Empty: Story = {
  args: {
    events: [],
  },
};

export const ErrorStream: Story = {
  args: {
    streamStatus: 'error',
  },
};
