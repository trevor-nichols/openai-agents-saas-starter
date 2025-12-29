import type {
  BillingEventHistoryResponse as BillingEventHistoryResponseDto,
  BillingEventInvoiceResponse,
  BillingEventResponse,
  BillingEventSubscriptionResponse,
  BillingEventUsageResponse,
  BillingPlanResponse,
  PaymentMethodResponse,
  PlanChangeResponse,
  PortalSessionResponse,
  StripeEventStatus,
  SubscriptionInvoiceListResponse,
  SubscriptionInvoiceResponse,
  UpcomingInvoiceLineResponse,
  UpcomingInvoicePreviewResponse,
  UsageTotalResponse,
} from '@/lib/api/client/types.gen';

export type BillingEventProcessingStatus = StripeEventStatus;

export type BillingEventSubscription = BillingEventSubscriptionResponse;

export type BillingEventInvoice = BillingEventInvoiceResponse;

export type BillingEventUsage = BillingEventUsageResponse;

export type BillingEvent = BillingEventResponse;

export type BillingStreamStatus = 'disabled' | 'connecting' | 'open' | 'error';

export type BillingPlan = BillingPlanResponse;

export type BillingPaymentMethod = PaymentMethodResponse;

export type BillingPortalSession = PortalSessionResponse;

export type UpcomingInvoicePreview = UpcomingInvoicePreviewResponse;

export type UpcomingInvoiceLine = UpcomingInvoiceLineResponse;

export type PlanChange = PlanChangeResponse;

export type BillingUsageTotal = UsageTotalResponse;

export type BillingInvoice = SubscriptionInvoiceResponse;

export type BillingInvoiceListResponse = SubscriptionInvoiceListResponse & {
  items: BillingInvoice[];
  next_offset: number | null;
  message?: string;
};

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
