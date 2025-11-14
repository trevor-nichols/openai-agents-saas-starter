import type {
  CancelSubscriptionRequest,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  UsageRecordRequest,
} from '@/lib/api/client/types.gen';

export type SubscriptionStartPayload = StartSubscriptionRequest;
export type SubscriptionUpdatePayload = UpdateSubscriptionRequest;
export type SubscriptionCancelPayload = CancelSubscriptionRequest;
export type UsageRecordPayload = UsageRecordRequest;

export type TenantSubscription = TenantSubscriptionResponse;

