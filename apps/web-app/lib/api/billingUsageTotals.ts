import type { BillingUsageTotal } from '@/types/billing';
import { apiV1Path } from '@/lib/apiPaths';
import {
  buildBillingHeaders,
  isBillingDisabled,
  parseBillingResponse,
  resolveBillingErrorMessage,
} from './billingUtils';

export interface FetchBillingUsageTotalsParams {
  tenantId: string;
  featureKeys?: string[] | null;
  periodStart?: string | null;
  periodEnd?: string | null;
  tenantRole?: string | null;
  signal?: AbortSignal;
}

export async function fetchBillingUsageTotals(
  params: FetchBillingUsageTotalsParams,
): Promise<BillingUsageTotal[]> {
  const {
    tenantId,
    featureKeys,
    periodStart,
    periodEnd,
    tenantRole = null,
    signal,
  } = params;

  if (!tenantId) {
    throw new Error('Tenant id is required to load usage totals.');
  }

  const search = new URLSearchParams();
  if (featureKeys && featureKeys.length > 0) {
    featureKeys.forEach((featureKey) => {
      search.append('feature_keys', featureKey);
    });
  }
  if (periodStart) {
    search.set('period_start', periodStart);
  }
  if (periodEnd) {
    search.set('period_end', periodEnd);
  }

  const baseUrl = apiV1Path(`/billing/tenants/${encodeURIComponent(tenantId)}/usage-totals`);
  const url = search.toString() ? `${baseUrl}?${search.toString()}` : baseUrl;

  const response = await fetch(url, {
    headers: buildBillingHeaders({ tenantRole }, false),
    cache: 'no-store',
    signal,
  });

  const payload = await parseBillingResponse<BillingUsageTotal[]>(response);
  if (isBillingDisabled(response.status, payload)) {
    return [];
  }

  if (!response.ok) {
    throw new Error(resolveBillingErrorMessage(payload, 'Failed to load usage totals.'));
  }

  return (payload ?? []) as BillingUsageTotal[];
}
