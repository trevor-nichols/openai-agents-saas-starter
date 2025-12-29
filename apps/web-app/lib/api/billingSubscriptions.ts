import type {
  SubscriptionCancelPayload,
  SubscriptionStartPayload,
  SubscriptionPlanChangePayload,
  SubscriptionPlanChangeResponse,
  SubscriptionUpdatePayload,
  TenantSubscription,
  UsageRecordPayload,
  SuccessNoData,
} from '@/lib/types/billing';
import { apiV1Path } from '@/lib/apiPaths';
import {
  buildBillingHeaders,
  isBillingDisabled,
  parseBillingResponse,
  resolveBillingErrorMessage,
} from './billingUtils';

interface RequestOptions {
  tenantRole?: string | null;
}

const subscriptionPath = (tenantId: string) => {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }
  return apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/subscription`);
};

const usagePath = (tenantId: string) => {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }
  return apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/usage`);
};

const cancelPath = (tenantId: string) => `${subscriptionPath(tenantId)}/cancel`;
const planPath = (tenantId: string) => `${subscriptionPath(tenantId)}/plan`;

export async function fetchTenantSubscription(
  tenantId: string,
  options?: RequestOptions,
): Promise<TenantSubscription> {
  const response = await fetch(subscriptionPath(tenantId), {
    method: 'GET',
    headers: buildBillingHeaders(options, false),
    cache: 'no-store',
  });

  const payload = await parseBillingResponse<TenantSubscription>(response);
  if (isBillingDisabled(response.status, payload)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(payload, 'Failed to load subscription.'));
  }

  if (!payload) {
    throw new Error('Subscription not found.');
  }

  return payload as TenantSubscription;
}

export async function startSubscriptionRequest(
  tenantId: string,
  payload: SubscriptionStartPayload,
  options?: RequestOptions,
): Promise<TenantSubscription> {
  const response = await fetch(subscriptionPath(tenantId), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseBillingResponse<TenantSubscription>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to start subscription.'));
  }
  if (!data) {
    throw new Error('Subscription start returned empty response.');
  }
  return data as TenantSubscription;
}

export async function updateSubscriptionRequest(
  tenantId: string,
  payload: SubscriptionUpdatePayload,
  options?: RequestOptions,
): Promise<TenantSubscription> {
  const response = await fetch(subscriptionPath(tenantId), {
    method: 'PATCH',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseBillingResponse<TenantSubscription>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to update subscription.'));
  }
  if (!data) {
    throw new Error('Subscription update returned empty response.');
  }
  return data as TenantSubscription;
}

export async function cancelSubscriptionRequest(
  tenantId: string,
  payload: SubscriptionCancelPayload,
  options?: RequestOptions,
): Promise<TenantSubscription> {
  const response = await fetch(cancelPath(tenantId), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseBillingResponse<TenantSubscription>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to cancel subscription.'));
  }
  if (!data) {
    throw new Error('Subscription cancel returned empty response.');
  }
  return data as TenantSubscription;
}

export async function changeSubscriptionPlanRequest(
  tenantId: string,
  payload: SubscriptionPlanChangePayload,
  options?: RequestOptions,
): Promise<SubscriptionPlanChangeResponse> {
  const response = await fetch(planPath(tenantId), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseBillingResponse<SubscriptionPlanChangeResponse>(response);
  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to change subscription plan.'));
  }
  if (!data) {
    throw new Error('Plan change returned empty response.');
  }
  return data as SubscriptionPlanChangeResponse;
}

export async function recordUsageRequest(
  tenantId: string,
  payload: UsageRecordPayload,
  options?: RequestOptions,
): Promise<void> {
  const response = await fetch(usagePath(tenantId), {
    method: 'POST',
    headers: buildBillingHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  const data = await parseBillingResponse<SuccessNoData>(response);

  if (isBillingDisabled(response.status, data)) {
    throw new Error('Billing is disabled.');
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(data, 'Failed to record usage.'));
  }
}
