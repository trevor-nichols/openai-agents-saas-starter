'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SubscriptionsTable } from '../components/SubscriptionsTable';
import { mockSubscriptions } from './fixtures';

const meta: Meta<typeof SubscriptionsTable> = {
  title: 'Status Ops/SubscriptionsTable',
  component: SubscriptionsTable,
  args: {
    subscriptions: mockSubscriptions,
    isLoading: false,
    isError: false,
    onRetry: () => console.log('retry subscriptions'),
    selectedId: mockSubscriptions[0]?.id,
  },
};

export default meta;

type Story = StoryObj<typeof SubscriptionsTable>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    isError: true,
    error: 'Failed to load status subscriptions',
  },
};

export const Empty: Story = {
  args: {
    subscriptions: [],
  },
};
