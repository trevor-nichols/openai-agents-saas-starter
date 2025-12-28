import type {
  CancelSubscriptionRequest,
  ChangeSubscriptionPlanRequest,
  PlanChangeResponse,
  PortalSessionRequest,
  PortalSessionResponse,
  PaymentMethodResponse,
  SetupIntentRequest,
  SetupIntentResponse,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  UsageRecordRequest,
  UpcomingInvoicePreviewRequest,
  UpcomingInvoicePreviewResponse,
  SuccessNoDataResponse,
} from '@/lib/api/client/types.gen';

export type SubscriptionStartPayload = StartSubscriptionRequest;
export type SubscriptionUpdatePayload = UpdateSubscriptionRequest;
export type SubscriptionCancelPayload = CancelSubscriptionRequest;
export type SubscriptionPlanChangePayload = ChangeSubscriptionPlanRequest;
export type UsageRecordPayload = UsageRecordRequest;

export type TenantSubscription = TenantSubscriptionResponse;

export type PlanChange = PlanChangeResponse;

export type BillingPortalSessionPayload = PortalSessionRequest;
export type BillingPortalSession = PortalSessionResponse;

export type BillingPaymentMethod = PaymentMethodResponse;
export type BillingSetupIntentPayload = SetupIntentRequest;
export type BillingSetupIntent = SetupIntentResponse;

export type UpcomingInvoicePreviewPayload = UpcomingInvoicePreviewRequest;
export type UpcomingInvoicePreview = UpcomingInvoicePreviewResponse;

export type SuccessNoData = SuccessNoDataResponse;
