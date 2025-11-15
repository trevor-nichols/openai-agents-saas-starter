import type {
  BillingEventHistoryResponse as BillingEventHistoryResponseDto,
  BillingEventInvoiceResponse,
  BillingEventResponse,
  BillingEventSubscriptionResponse,
  BillingEventUsageResponse,
  BillingPlanResponse,
  StripeEventStatus,
} from '@/lib/api/client/types.gen';

export type BillingEventProcessingStatus = StripeEventStatus;

export type BillingEventSubscription = BillingEventSubscriptionResponse;

export type BillingEventInvoice = BillingEventInvoiceResponse;

export type BillingEventUsage = BillingEventUsageResponse;

export type BillingEvent = BillingEventResponse;

export type BillingStreamStatus = 'disabled' | 'connecting' | 'open' | 'error';

export type BillingPlan = BillingPlanResponse;

export interface BillingPlanListResponse {
  success: boolean;
  plans?: BillingPlan[];
  error?: string;
}

export type BillingEventHistoryResponse = BillingEventHistoryResponseDto & {
  items: BillingEvent[];
  next_cursor: string | null;
  message?: string;
};
