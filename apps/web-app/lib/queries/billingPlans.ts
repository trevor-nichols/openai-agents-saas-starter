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

export function useBillingPlans(): UseBillingPlansResult {
  const { flags } = useFeatureFlags();
  const billingEnabled = Boolean(flags?.billingEnabled);
  const {
    data = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.billing.plans(),
    queryFn: fetchBillingPlans,
    staleTime: 5 * 60 * 1000,
    enabled: billingEnabled,
  });

  return {
    plans: data,
    isLoading,
    error: error?.message ?? null,
    refetch: () => refetch().then(() => undefined),
  };
}
