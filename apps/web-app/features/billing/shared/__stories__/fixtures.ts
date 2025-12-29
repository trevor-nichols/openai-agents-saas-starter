import type { PlanSnapshot, InvoiceSummary, UsageRow } from '../types';
import type { BillingEvent, BillingPlan, BillingStreamStatus, BillingPaymentMethod, UpcomingInvoicePreview } from '@/types/billing';
import type { TenantSubscription } from '@/lib/types/billing';

const now = new Date();
const twoDaysMs = 2 * 24 * 60 * 60 * 1000;

export const mockStreamStatus: BillingStreamStatus = 'open';

export const mockPlanSnapshot: PlanSnapshot = {
  planCode: 'pro_plus',
  planStatus: 'active',
  seatCount: 15,
  autoRenewLabel: 'Enabled',
  currentPeriodLabel: 'Dec 1 – Dec 31',
  trialEndsLabel: '—',
  statusTone: 'positive',
  statusLabel: 'Active',
};

export const mockInvoiceSummary: InvoiceSummary = {
  amountLabel: '$1,249.00',
  statusLabel: 'draft',
  reason: 'Usage',
  collectionMethod: 'auto',
  invoiceUrl: 'https://billing.example.com/invoices/inv_123',
};

export const mockUsageRows: UsageRow[] = [
  { key: 'search-1', feature: 'vector_search', quantity: '12,450', amount: '$124.50', period: 'Dec 8 – Dec 9' },
  { key: 'genai-2', feature: 'gen_ai_tokens', quantity: '3.4M', amount: '$980.00', period: 'Dec 8 – Dec 9' },
  { key: 'storage-3', feature: 'artifact_storage', quantity: '240 GB', amount: '$72.00', period: 'Dec 7 – Dec 8' },
];

export const mockBillingEvents: BillingEvent[] = [
  {
    stripe_event_id: 'evt_inv_paid',
    tenant_id: 'tenant-1',
    event_type: 'invoice.paid',
    occurred_at: new Date(now.getTime() - twoDaysMs).toISOString(),
    summary: 'Invoice paid',
    status: 'processed',
    invoice: {
      invoice_id: 'inv_123',
      amount_due_cents: 124900,
      currency: 'USD',
      status: 'paid',
      billing_reason: 'subscription_cycle',
      collection_method: 'charge_automatically',
      hosted_invoice_url: 'https://billing.example.com/invoices/inv_123',
    },
    subscription: undefined,
    usage: [],
  },
  {
    stripe_event_id: 'evt_usage',
    tenant_id: 'tenant-1',
    event_type: 'customer.usage_reported',
    occurred_at: new Date(now.getTime() - twoDaysMs / 2).toISOString(),
    summary: 'Usage recorded',
    status: 'processed',
    invoice: undefined,
    subscription: undefined,
    usage: [
      { feature_key: 'vector_search', quantity: 2000, amount_cents: 20000, period_start: '2025-12-07', period_end: '2025-12-08' },
      { feature_key: 'gen_ai_tokens', quantity: 500000, amount_cents: 50000, period_start: '2025-12-07', period_end: '2025-12-08' },
    ],
  },
  {
    stripe_event_id: 'evt_sub_updated',
    tenant_id: 'tenant-1',
    event_type: 'customer.subscription.updated',
    occurred_at: now.toISOString(),
    summary: 'Seats increased',
    status: 'processed',
    subscription: {
      plan_code: 'pro_plus',
      status: 'active',
      seat_count: 15,
      auto_renew: true,
      current_period_start: '2025-12-01',
      current_period_end: '2025-12-31',
      trial_ends_at: null,
      cancel_at: null,
    },
    invoice: undefined,
    usage: [],
  },
];

export const mockSubscription: TenantSubscription = {
  tenant_id: 'tenant-1',
  plan_code: 'pro_plus',
  status: 'active',
  auto_renew: true,
  seat_count: 15,
  billing_email: 'billing@example.com',
  starts_at: '2025-10-01',
  current_period_start: '2025-12-01',
  current_period_end: '2025-12-31',
  trial_ends_at: null,
  cancel_at: null,
  metadata: {},
};

export const mockPlans: BillingPlan[] = [
  {
    code: 'starter',
    name: 'Starter',
    price_cents: 4900,
    currency: 'USD',
    interval: 'month',
    interval_count: 1,
    trial_days: 14,
    seat_included: 3,
    features: [
      { key: 'seat', display_name: 'Seats', description: 'Up to 3 seats', is_metered: false },
      { key: 'search', display_name: 'Vector search', description: 'Included', is_metered: false },
    ],
    is_active: true,
  },
  {
    code: 'pro_plus',
    name: 'Pro Plus',
    price_cents: 24900,
    currency: 'USD',
    interval: 'month',
    interval_count: 1,
    trial_days: 0,
    seat_included: 10,
    features: [
      { key: 'seat', display_name: 'Seats', description: 'Up to 10 seats', is_metered: false },
      { key: 'genai', display_name: 'GenAI tokens', description: 'Discounted usage', is_metered: true },
      { key: 'search', display_name: 'Vector search', description: 'Included', is_metered: false },
    ],
    is_active: true,
  },
  {
    code: 'legacy',
    name: 'Legacy',
    price_cents: 9900,
    currency: 'USD',
    interval: 'month',
    interval_count: 1,
    trial_days: 0,
    seat_included: 5,
    features: [],
    is_active: false,
  },
];

export const mockPaymentMethods: BillingPaymentMethod[] = [
  {
    id: 'pm_visa',
    brand: 'visa',
    last4: '4242',
    exp_month: 12,
    exp_year: 2027,
    is_default: true,
  },
  {
    id: 'pm_mastercard',
    brand: 'mastercard',
    last4: '4444',
    exp_month: 6,
    exp_year: 2026,
    is_default: false,
  },
];

export const mockUpcomingInvoicePreview: UpcomingInvoicePreview = {
  plan_code: 'pro_plus',
  plan_name: 'Pro Plus',
  seat_count: 15,
  invoice_id: 'inv_preview_123',
  amount_due_cents: 124900,
  currency: 'USD',
  period_start: '2025-12-01',
  period_end: '2025-12-31',
  lines: [
    {
      description: 'Base subscription',
      amount_cents: 99000,
      currency: 'USD',
      quantity: 1,
      unit_amount_cents: 99000,
      price_id: 'price_base',
    },
    {
      description: 'Additional seats',
      amount_cents: 25900,
      currency: 'USD',
      quantity: 5,
      unit_amount_cents: 5180,
      price_id: 'price_seat',
    },
  ],
};
