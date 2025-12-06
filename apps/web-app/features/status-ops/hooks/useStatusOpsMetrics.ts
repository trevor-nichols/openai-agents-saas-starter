import { useMemo } from 'react';

import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

export interface StatusOpsMetrics {
  total: number;
  active: number;
  pending: number;
  emailCount: number;
  webhookCount: number;
  tenantCount: number;
}

export function deriveStatusOpsMetrics(subscriptions: StatusSubscriptionSummary[]): StatusOpsMetrics {
  const total = subscriptions.length;
  const active = subscriptions.filter((s) => s.status === 'active').length;
  const pending = subscriptions.filter((s) => s.status === 'pending_verification').length;
  const emailCount = subscriptions.filter((s) => s.channel === 'email').length;
  const webhookCount = subscriptions.filter((s) => s.channel === 'webhook').length;
  const tenantCount = new Set(
    subscriptions
      .filter((s) => s.tenantId)
      .map((s) => s.tenantId as string),
  ).size;

  return {
    total,
    active,
    pending,
    emailCount,
    webhookCount,
    tenantCount,
  };
}

export function useStatusOpsMetrics(subscriptions: StatusSubscriptionSummary[]): StatusOpsMetrics {
  return useMemo(() => deriveStatusOpsMetrics(subscriptions), [subscriptions]);
}
