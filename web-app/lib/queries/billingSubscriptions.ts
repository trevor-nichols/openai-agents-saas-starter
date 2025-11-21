import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type {
  SubscriptionCancelPayload,
  SubscriptionStartPayload,
  SubscriptionUpdatePayload,
  TenantSubscription,
  UsageRecordPayload,
} from '@/lib/types/billing';
import {
  cancelSubscriptionRequest,
  fetchTenantSubscription,
  recordUsageRequest,
  startSubscriptionRequest,
  updateSubscriptionRequest,
} from '@/lib/api/billingSubscriptions';
import { queryKeys } from './keys';
import { billingEnabled } from '@/lib/config/features';

interface SubscriptionOptions {
  tenantId: string | null;
  tenantRole?: string | null;
}

export function useTenantSubscription(options: SubscriptionOptions) {
  const { tenantId, tenantRole = null } = options;
  const enabled = billingEnabled && Boolean(tenantId);

  const query = useQuery({
    queryKey: tenantId
      ? [...queryKeys.billing.all, 'subscription', tenantId]
      : [...queryKeys.billing.all, 'subscription'],
    queryFn: () => fetchTenantSubscription(tenantId as string, { tenantRole }),
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
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return startSubscriptionRequest(tenantId, payload, { tenantRole });
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
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return updateSubscriptionRequest(tenantId, payload, { tenantRole });
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
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return cancelSubscriptionRequest(tenantId, payload, { tenantRole });
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
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      await recordUsageRequest(tenantId, payload, { tenantRole });
    },
  });
}
