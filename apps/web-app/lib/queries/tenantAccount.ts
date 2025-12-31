import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { fetchTenantAccount, updateTenantAccount } from '@/lib/api/tenantAccount';
import type { TenantAccount, TenantAccountSelfUpdateInput } from '@/types/tenantAccount';

import { queryKeys } from './keys';

export function useTenantAccountQuery(options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.tenant.account(),
    queryFn: fetchTenantAccount,
    staleTime: 60 * 1000,
    enabled: options?.enabled ?? true,
  });
}

export function useUpdateTenantAccountMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (payload: TenantAccountSelfUpdateInput) => updateTenantAccount(payload),
    onMutate: async (payload) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.tenant.account() });
      const previous = queryClient.getQueryData<TenantAccount>(queryKeys.tenant.account());
      if (!previous) {
        return { previous: null };
      }
      const optimistic: TenantAccount = {
        ...previous,
        name: payload.name,
      };
      queryClient.setQueryData(queryKeys.tenant.account(), optimistic);
      return { previous };
    },
    onError: (_error, _variables, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.tenant.account(), context.previous);
      }
    },
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.tenant.account(), data);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.tenant.account() }).catch(() => null);
    },
  });
}
