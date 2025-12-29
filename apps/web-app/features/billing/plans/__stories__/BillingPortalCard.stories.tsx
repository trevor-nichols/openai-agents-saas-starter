'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { BillingPortalCard } from '../components/BillingPortalCard';

const meta: Meta<typeof BillingPortalCard> = {
  title: 'Billing/BillingPortalCard',
  component: BillingPortalCard,
  args: {
    tenantId: 'tenant-1',
    billingEmail: 'billing@example.com',
  },
};

export default meta;

type Story = StoryObj<typeof BillingPortalCard>;

export const Default: Story = {};

export const Disabled: Story = {
  args: {
    tenantId: null,
  },
};
