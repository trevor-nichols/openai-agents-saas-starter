'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SubscriptionSettingsCard } from '../components/SubscriptionSettingsCard';
import { mockSubscription } from './fixtures';

const meta: Meta<typeof SubscriptionSettingsCard> = {
  title: 'Billing/SubscriptionSettingsCard',
  component: SubscriptionSettingsCard,
  args: {
    tenantId: 'tenant-1',
    subscription: mockSubscription,
    isLoading: false,
    error: null,
    onRetry: () => {},
  },
};

export default meta;

type Story = StoryObj<typeof SubscriptionSettingsCard>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoading: true,
  },
};

export const Empty: Story = {
  args: {
    subscription: null,
  },
};

export const ErrorState: Story = {
  args: {
    error: new Error('Failed to load subscription'),
  },
};
