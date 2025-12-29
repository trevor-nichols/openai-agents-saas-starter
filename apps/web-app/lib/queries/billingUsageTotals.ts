import { useQuery } from '@tanstack/react-query';

import { fetchBillingUsageTotals } from '@/lib/api/billingUsageTotals';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { billingEnabled } from '@/lib/config/features';
import type { BillingUsageTotal } from '@/types/billing';
import { queryKeys } from './keys';

export interface UseBillingUsageTotalsOptions {
  featureKeys?: string[] | null;
  periodStart?: string | null;
  periodEnd?: string | null;
  tenantRole?: string | null;
}

export interface UseBillingUsageTotalsResult {
  totals: BillingUsageTotal[];
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

function normalizeFeatureKeys(featureKeys?: string[] | null): string[] {
  if (!featureKeys || featureKeys.length === 0) {
    return [];
  }
  return Array.from(new Set(featureKeys.map((key) => key.trim()).filter(Boolean))).sort();
}

export function useBillingUsageTotals(
  options?: UseBillingUsageTotalsOptions,
): UseBillingUsageTotalsResult {
  const meta = readClientSessionMeta();
  const tenantId = meta?.tenantId ?? null;
  const normalizedFeatureKeys = normalizeFeatureKeys(options?.featureKeys);
  const periodStart = options?.periodStart ?? null;
  const periodEnd = options?.periodEnd ?? null;

  const query = useQuery({
    queryKey: queryKeys.billing.usageTotals(tenantId, {
      featureKeys: normalizedFeatureKeys,
      periodStart,
      periodEnd,
    }),
    queryFn: () => {
      if (!tenantId) {
        return Promise.resolve([] as BillingUsageTotal[]);
      }
      return fetchBillingUsageTotals({
        tenantId,
        featureKeys: normalizedFeatureKeys,
        periodStart,
        periodEnd,
        tenantRole: options?.tenantRole ?? null,
      });
    },
    enabled: billingEnabled && Boolean(tenantId),
    staleTime: 30 * 1000,
  });

  return {
    totals: (query.data as BillingUsageTotal[] | undefined) ?? [],
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error : null,
    refetch: () => query.refetch().then(() => undefined),
  };
}
