import { useQuery } from '@tanstack/react-query';

import { fetchBillingPlans } from '@/lib/api/billingPlans';
import { queryKeys } from './keys';
import type { BillingPlan } from '@/types/billing';
import { useFeatureFlags } from '@/lib/queries/featureFlags';

interface UseBillingPlansResult {
  plans: BillingPlan[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

function useBillingPlansQuery(enabled: boolean, key: readonly unknown[]): UseBillingPlansResult {
  const {
    data = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: key,
    queryFn: fetchBillingPlans,
    staleTime: 5 * 60 * 1000,
    enabled,
  });

  return {
    plans: data,
    isLoading,
    error: error?.message ?? null,
    refetch: () => refetch().then(() => undefined),
  };
}

export function useBillingPlans(): UseBillingPlansResult {
  const { flags } = useFeatureFlags();
  const billingEnabled = Boolean(flags?.billingEnabled);
  return useBillingPlansQuery(billingEnabled, queryKeys.billing.plans());
}

export function usePublicBillingPlans(): UseBillingPlansResult {
  return useBillingPlansQuery(true, queryKeys.billing.publicPlans());
}
