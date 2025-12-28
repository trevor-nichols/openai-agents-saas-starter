import type {
  CancelSubscriptionRequest,
  ChangeSubscriptionPlanRequest,
  PlanChangeResponse as PlanChangeResponseDto,
  PlanChangeTiming as PlanChangeTimingDto,
  StartSubscriptionRequest,
  TenantSubscriptionResponse,
  UpdateSubscriptionRequest,
  UsageRecordRequest,
} from '@/lib/api/client/types.gen';

export type SubscriptionStartPayload = StartSubscriptionRequest;
export type SubscriptionUpdatePayload = UpdateSubscriptionRequest;
export type SubscriptionCancelPayload = CancelSubscriptionRequest;
export type UsageRecordPayload = UsageRecordRequest;
export type SubscriptionPlanChangePayload = ChangeSubscriptionPlanRequest;
export type SubscriptionPlanChangeResponse = PlanChangeResponseDto;
export type PlanChangeTiming = PlanChangeTimingDto;

export type TenantSubscription = TenantSubscriptionResponse;
