/**
 * Billing event types
 */

export type BillingEventSubscription = {
  plan_code: string;
  status: string;
  seat_count?: number | null;
  auto_renew: boolean;
  current_period_start?: string | null;
  current_period_end?: string | null;
  trial_ends_at?: string | null;
  cancel_at?: string | null;
};

export type BillingEventInvoice = {
  invoice_id: string;
  status: string;
  amount_due_cents: number;
  currency: string;
  billing_reason?: string | null;
  hosted_invoice_url?: string | null;
  collection_method?: string | null;
  period_start?: string | null;
  period_end?: string | null;
};

export type BillingEventUsage = {
  feature_key: string;
  quantity: number;
  period_start?: string | null;
  period_end?: string | null;
  amount_cents?: number | null;
};

import type { BillingPlanResponse } from '@/lib/api/client/types.gen';

export type BillingEvent = {
  tenant_id: string;
  event_type: string;
  stripe_event_id: string;
  occurred_at: string;
  summary?: string | null;
  status: string;
  subscription?: BillingEventSubscription | null;
  invoice?: BillingEventInvoice | null;
  usage?: BillingEventUsage[];
};

export type BillingStreamStatus = 'disabled' | 'connecting' | 'open' | 'error';

export type BillingPlan = BillingPlanResponse;

export interface BillingPlanListResponse {
  success: boolean;
  plans?: BillingPlan[];
  error?: string;
}

export interface BillingEventHistoryResponse {
  items: BillingEvent[];
  next_cursor: string | null;
  message?: string;
}
