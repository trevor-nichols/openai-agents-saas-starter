import type { BillingEvent } from '@/types/billing';
import { Sparkles, TrendingUp, WalletMinimal } from 'lucide-react';

import type { ActivityFeedItem, BillingPreviewSummary, DashboardKpi } from '../types';
import { QUICK_ACTIONS } from '../constants';

const now = Date.now();

export const dashboardKpis: DashboardKpi[] = [
  {
    id: 'agents-online',
    label: 'Agents online',
    value: '8',
    helperText: '2 off duty',
    icon: <Sparkles className="h-4 w-4" />,
    trend: {
      value: '80% util',
      tone: 'positive',
      label: '10 registered',
    },
  },
  {
    id: 'activity-volume',
    label: 'Recent activity',
    value: '24',
    helperText: 'Live audit stream',
    icon: <TrendingUp className="h-4 w-4" />,
    trend: {
      value: 'Live',
      tone: 'positive',
      label: 'Workflow run completed',
    },
  },
  {
    id: 'billing-events',
    label: 'Billing events',
    value: '5',
    helperText: 'Last 20 retained',
    icon: <WalletMinimal className="h-4 w-4" />,
    trend: {
      value: 'Open stream',
      tone: 'neutral',
      label: 'Invoice created',
    },
  },
];

export const activityItems: ActivityFeedItem[] = [
  {
    id: 'act-1',
    title: 'Workflow run finished',
    detail: 'triage_agent completed customer triage',
    status: 'success',
    timestamp: new Date(now - 2 * 60 * 1000).toISOString(),
    metadataSummary: 'duration 32s',
  },
  {
    id: 'act-2',
    title: 'Container deployed',
    detail: 'analytics-sandbox ready for traffic',
    status: 'pending',
    timestamp: new Date(now - 15 * 60 * 1000).toISOString(),
    metadataSummary: 'memory 8g',
  },
  {
    id: 'act-3',
    title: 'Subscription update failed',
    detail: 'Stripe webhook retry scheduled',
    status: 'failure',
    timestamp: new Date(now - 45 * 60 * 1000).toISOString(),
  },
];

const billingEvents: BillingEvent[] = [
  {
    tenant_id: 'tenant-123',
    event_type: 'invoice.created',
    stripe_event_id: 'evt_1',
    occurred_at: new Date(now - 3 * 60 * 60 * 1000).toISOString(),
    status: 'processed',
    summary: 'Invoice created',
    invoice: {
      invoice_id: 'inv_123',
      status: 'draft',
      amount_due_cents: 4200,
      currency: 'USD',
      billing_reason: 'subscription_create',
      hosted_invoice_url: 'https://dashboard.stripe.com/test/invoices/inv_123',
      collection_method: 'charge_automatically',
      period_start: new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString(),
      period_end: new Date(now + 23 * 24 * 60 * 60 * 1000).toISOString(),
    },
  },
  {
    tenant_id: 'tenant-123',
    event_type: 'customer.subscription.updated',
    stripe_event_id: 'evt_2',
    occurred_at: new Date(now - 5 * 60 * 60 * 1000).toISOString(),
    status: 'processed',
    summary: 'Plan upgraded to Pro',
    subscription: {
      plan_code: 'pro',
      status: 'active',
      seat_count: 5,
      auto_renew: true,
      current_period_start: new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString(),
      current_period_end: new Date(now + 23 * 24 * 60 * 60 * 1000).toISOString(),
    },
  },
];

export const billingPreviewSummary: BillingPreviewSummary = {
  planCode: 'Pro',
  planStatus: 'active',
  streamStatus: 'open',
  nextInvoiceLabel: '$42.00',
  latestEvents: billingEvents,
};

export const quickActions = QUICK_ACTIONS;
