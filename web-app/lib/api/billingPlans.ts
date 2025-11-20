import type { BillingPlan, BillingPlanListResponse } from '@/types/billing';

export async function fetchBillingPlans(): Promise<BillingPlan[]> {
  const response = await fetch('/api/billing/plans', { cache: 'no-store' });
  const payload = (await response.json()) as BillingPlanListResponse;

  if (response.status === 404) {
    return [];
  }

  if (!response.ok) {
    throw new Error(payload.error || 'Failed to load billing plans');
  }

  if (!payload.success || !payload.plans) {
    throw new Error(payload.error || 'No plans returned from API');
  }

  return payload.plans;
}
