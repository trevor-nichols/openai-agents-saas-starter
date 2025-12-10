'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { CurrentSubscriptionCard } from '../components/CurrentSubscriptionCard';
import { mockSubscription } from './fixtures';

const meta: Meta<typeof CurrentSubscriptionCard> = {
  title: 'Billing/CurrentSubscriptionCard',
  component: CurrentSubscriptionCard,
  args: {
    subscription: mockSubscription,
    isLoading: false,
    error: null,
    onRetry: () => console.log('retry subscription'),
  },
};

export default meta;

type Story = StoryObj<typeof CurrentSubscriptionCard>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const ErrorState: Story = {
  args: {
    error: new Error('Failed to load subscription'),
  },
};

export const Empty: Story = {
  args: {
    subscription: null,
  },
};
