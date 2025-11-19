import type {
  SubscriptionCancelPayload,
  SubscriptionStartPayload,
  SubscriptionUpdatePayload,
  TenantSubscription,
  UsageRecordPayload,
} from '@/lib/types/billing';

interface RequestOptions {
  tenantRole?: string | null;
}

type ErrorPayload = {
  message?: string;
  error?: string;
};

const subscriptionPath = (tenantId: string) => {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }
  return `/api/billing/tenants/${encodeURIComponent(tenantId)}/subscription`;
};

const usagePath = (tenantId: string) => {
  if (!tenantId || tenantId.trim().length === 0) {
    throw new Error('Tenant id is required.');
  }
  return `/api/billing/tenants/${encodeURIComponent(tenantId)}/usage`;
};

const cancelPath = (tenantId: string) => `${subscriptionPath(tenantId)}/cancel`;

function buildHeaders(options: RequestOptions | undefined, includeJson = false): HeadersInit {
  const headers: Record<string, string> = {};
  if (includeJson) {
    headers['Content-Type'] = 'application/json';
  }
  if (options?.tenantRole) {
    headers['X-Tenant-Role'] = options.tenantRole;
  }
  return headers;
}

function resolveErrorMessage(payload: unknown, fallbackMessage: string): string {
  if (payload && typeof payload === 'object') {
    const candidate = payload as ErrorPayload;
    if (candidate.message && typeof candidate.message === 'string') {
      return candidate.message;
    }
    if (candidate.error && typeof candidate.error === 'string') {
      return candidate.error;
    }
  }
  return fallbackMessage;
}

async function parseResponse<T>(response: Response): Promise<T | ErrorPayload> {
  try {
    return (await response.json()) as T;
  } catch (_error) {
    return {};
  }
}

export async function fetchTenantSubscription(
  tenantId: string,
  options?: RequestOptions,
): Promise<TenantSubscription> {
  const response = await fetch(subscriptionPath(tenantId), {
    method: 'GET',
    headers: buildHeaders(options, false),
    cache: 'no-store',
  });

  const payload = await parseResponse<TenantSubscription>(response);

  if (!response.ok) {
    throw new Error(resolveErrorMessage(payload, 'Failed to load subscription.'));
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
    headers: buildHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseResponse<TenantSubscription>(response);

  if (!response.ok) {
    throw new Error(resolveErrorMessage(data, 'Failed to start subscription.'));
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
    headers: buildHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseResponse<TenantSubscription>(response);

  if (!response.ok) {
    throw new Error(resolveErrorMessage(data, 'Failed to update subscription.'));
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
    headers: buildHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  const data = await parseResponse<TenantSubscription>(response);

  if (!response.ok) {
    throw new Error(resolveErrorMessage(data, 'Failed to cancel subscription.'));
  }
  if (!data) {
    throw new Error('Subscription cancel returned empty response.');
  }
  return data as TenantSubscription;
}

export async function recordUsageRequest(
  tenantId: string,
  payload: UsageRecordPayload,
  options?: RequestOptions,
): Promise<void> {
  const response = await fetch(usagePath(tenantId), {
    method: 'POST',
    headers: buildHeaders(options, true),
    cache: 'no-store',
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const data = await parseResponse<ErrorPayload>(response);
    throw new Error(resolveErrorMessage(data, 'Failed to record usage.'));
  }
}
