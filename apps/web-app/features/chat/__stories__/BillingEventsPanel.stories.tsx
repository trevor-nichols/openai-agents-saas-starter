import type { Meta, StoryObj } from '@storybook/react';

import { BillingEventsPanel } from '../components/BillingEventsPanel';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';

const now = new Date();

const billingEvents: BillingEvent[] = [
  {
    tenant_id: 'tenant-1',
    stripe_event_id: 'evt_1',
    event_type: 'invoice.created',
    occurred_at: new Date(now.getTime() - 2 * 60 * 1000).toISOString(),
    status: 'processed',
    invoice: {
      invoice_id: 'inv_123',
      amount_due_cents: 4200,
      currency: 'USD',
      hosted_invoice_url: 'https://stripe.example/inv_123',
    },
    summary: 'Invoice created',
  } as BillingEvent,
  {
    tenant_id: 'tenant-1',
    stripe_event_id: 'evt_2',
    event_type: 'customer.subscription.updated',
    occurred_at: new Date(now.getTime() - 5 * 60 * 1000).toISOString(),
    status: 'processed',
    subscription: {
      plan_code: 'pro',
      status: 'active',
      auto_renew: true,
      current_period_start: new Date(now.getTime() - 10 * 60 * 1000).toISOString(),
      current_period_end: new Date(now.getTime() + 20 * 60 * 1000).toISOString(),
    },
    summary: 'Subscription updated',
  } as BillingEvent,
];

const meta: Meta<typeof BillingEventsPanel> = {
  title: 'Chat/BillingEventsPanel',
  component: BillingEventsPanel,
  args: {
    events: billingEvents,
    status: 'open' as BillingStreamStatus,
  },
};

export default meta;

type Story = StoryObj<typeof BillingEventsPanel>;

export const LiveFeed: Story = {};

export const Connecting: Story = {
  args: {
    status: 'connecting',
  },
};

export const ErrorState: Story = {
  args: {
    events: [],
    status: 'error',
  },
};

export const EmptyState: Story = {
  args: {
    events: [],
    status: 'open',
  },
};
