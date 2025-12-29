import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createSetupIntentRequest,
  detachPaymentMethodRequest,
  fetchPaymentMethods,
  setDefaultPaymentMethodRequest,
} from '@/lib/api/billingPaymentMethods';
import type {
  BillingPaymentMethod,
  BillingSetupIntent,
  BillingSetupIntentPayload,
  SuccessNoData,
} from '@/lib/types/billing';
import { billingEnabled } from '@/lib/config/features';
import { queryKeys } from './keys';

interface PaymentMethodOptions {
  tenantId: string | null;
  tenantRole?: string | null;
}

interface UsePaymentMethodsResult {
  paymentMethods: BillingPaymentMethod[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export function usePaymentMethodsQuery(options: PaymentMethodOptions): UsePaymentMethodsResult {
  const { tenantId, tenantRole = null } = options;
  const enabled = billingEnabled && Boolean(tenantId);

  const query = useQuery({
    queryKey: queryKeys.billing.paymentMethods(tenantId),
    queryFn: () => fetchPaymentMethods(tenantId as string, { tenantRole }),
    enabled,
    staleTime: 30 * 1000,
  });

  return {
    paymentMethods: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error instanceof Error ? query.error.message : null,
    refetch: () => query.refetch().then(() => undefined),
  };
}

export function useCreateSetupIntentMutation(options: PaymentMethodOptions) {
  const { tenantId, tenantRole = null } = options;

  return useMutation<BillingSetupIntent, Error, BillingSetupIntentPayload>({
    mutationFn: async (payload: BillingSetupIntentPayload) => {
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return createSetupIntentRequest(tenantId, payload, { tenantRole });
    },
  });
}

export function useSetDefaultPaymentMethodMutation(options: PaymentMethodOptions) {
  const queryClient = useQueryClient();
  const { tenantId, tenantRole = null } = options;

  return useMutation<SuccessNoData, Error, { paymentMethodId: string }>({
    mutationFn: async ({ paymentMethodId }) => {
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return setDefaultPaymentMethodRequest(tenantId, paymentMethodId, { tenantRole });
    },
    onSuccess: () => {
      if (!tenantId) return;
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.paymentMethods(tenantId) });
    },
  });
}

export function useDetachPaymentMethodMutation(options: PaymentMethodOptions) {
  const queryClient = useQueryClient();
  const { tenantId, tenantRole = null } = options;

  return useMutation<SuccessNoData, Error, { paymentMethodId: string }>({
    mutationFn: async ({ paymentMethodId }) => {
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return detachPaymentMethodRequest(tenantId, paymentMethodId, { tenantRole });
    },
    onSuccess: () => {
      if (!tenantId) return;
      queryClient.invalidateQueries({ queryKey: queryKeys.billing.paymentMethods(tenantId) });
    },
  });
}
