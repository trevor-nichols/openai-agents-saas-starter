import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/lib/queries/keys';
import type { TenantSettings, TenantSettingsUpdateInput } from '@/types/tenantSettings';

import { fetchTenantSettings, updateTenantSettings } from './tenantSettings-api';

function mergeSettings(current: TenantSettings, patch: Partial<TenantSettingsUpdateInput>): TenantSettingsUpdateInput {
  return {
    billingContacts: patch.billingContacts ?? current.billingContacts,
    billingWebhookUrl: patch.billingWebhookUrl !== undefined ? patch.billingWebhookUrl : current.billingWebhookUrl,
    planMetadata: patch.planMetadata ?? { ...current.planMetadata },
    flags: patch.flags ?? { ...current.flags },
  };
}

export function useTenantSettingsQuery(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.tenant.settings(),
    queryFn: fetchTenantSettings,
    staleTime: 60 * 1000,
    enabled: options?.enabled ?? true,
  });
}

export function useUpdateTenantSettingsMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (patch: Partial<TenantSettingsUpdateInput>) => {
      const current = queryClient.getQueryData<TenantSettings>(queryKeys.tenant.settings());
      if (!current) {
        throw new Error('Tenant settings are not loaded yet.');
      }
      const payload = mergeSettings(current, patch);
      return updateTenantSettings(payload);
    },
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.tenant.settings() });
      const previous = queryClient.getQueryData<TenantSettings>(queryKeys.tenant.settings());
      if (!previous) {
        return { previous: null };
      }
      const optimisticPayload = mergeSettings(previous, patch);
      const optimistic: TenantSettings = {
        ...previous,
        billingContacts: optimisticPayload.billingContacts,
        billingWebhookUrl: optimisticPayload.billingWebhookUrl,
        planMetadata: optimisticPayload.planMetadata,
        flags: optimisticPayload.flags,
      };
      queryClient.setQueryData(queryKeys.tenant.settings(), optimistic);
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.tenant.settings(), context.previous);
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.tenant.settings(), data);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tenant.settings() }).catch(() => null);
    },
  });
}
