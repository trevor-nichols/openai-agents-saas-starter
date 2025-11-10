import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type {
  SubscriptionCancelPayload,
  SubscriptionStartPayload,
  SubscriptionUpdatePayload,
  TenantSubscription,
  UsageRecordPayload,
} from '@/lib/types/billing';
import {
  getTenantSubscription,
  startTenantSubscription,
  updateTenantSubscription,
  cancelTenantSubscription,
  recordTenantUsage,
} from '@/lib/server/services/billing';
import { queryKeys } from './keys';

interface SubscriptionOptions {
  tenantId: string | null;
  tenantRole?: string | null;
}

export function useTenantSubscription(options: SubscriptionOptions) {
  const { tenantId, tenantRole = null } = options;
  const enabled = Boolean(tenantId);

  const query = useQuery({
    queryKey: tenantId
      ? [...queryKeys.billing.all, 'subscription', tenantId]
      : [...queryKeys.billing.all, 'subscription'],
    queryFn: () => getTenantSubscription(tenantId as string, { tenantRole }),
    enabled,
    staleTime: 30 * 1000,
  });

  return {
    subscription: (query.data as TenantSubscription | undefined) ?? null,
    isLoadingSubscription: query.isLoading,
    subscriptionError: query.error instanceof Error ? query.error : null,
    refetchSubscription: query.refetch,
  };
}

export function useStartSubscriptionMutation(options: SubscriptionOptions) {
  const queryClient = useQueryClient();
  const { tenantId, tenantRole = null } = options;

  return useMutation({
    mutationFn: async (payload: SubscriptionStartPayload) => {
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return startTenantSubscription(tenantId, payload, { tenantRole });
    },
    onSuccess: (subscription) => {
      if (!tenantId) return;
      queryClient.setQueryData(
        [...queryKeys.billing.all, 'subscription', tenantId],
        subscription,
      );
    },
  });
}

export function useUpdateSubscriptionMutation(options: SubscriptionOptions) {
  const queryClient = useQueryClient();
  const { tenantId, tenantRole = null } = options;

  return useMutation({
    mutationFn: async (payload: SubscriptionUpdatePayload) => {
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return updateTenantSubscription(tenantId, payload, { tenantRole });
    },
    onSuccess: (subscription) => {
      if (!tenantId) return;
      queryClient.setQueryData(
        [...queryKeys.billing.all, 'subscription', tenantId],
        subscription,
      );
    },
  });
}

export function useCancelSubscriptionMutation(options: SubscriptionOptions) {
  const queryClient = useQueryClient();
  const { tenantId, tenantRole = null } = options;

  return useMutation({
    mutationFn: async (payload: SubscriptionCancelPayload) => {
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return cancelTenantSubscription(tenantId, payload, { tenantRole });
    },
    onSuccess: (subscription) => {
      if (!tenantId) return;
      queryClient.setQueryData(
        [...queryKeys.billing.all, 'subscription', tenantId],
        subscription,
      );
    },
  });
}

export function useUsageRecordMutation(options: SubscriptionOptions) {
  const { tenantId, tenantRole = null } = options;

  return useMutation({
    mutationFn: async (payload: UsageRecordPayload) => {
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      await recordTenantUsage(tenantId, payload, { tenantRole });
    },
  });
}

