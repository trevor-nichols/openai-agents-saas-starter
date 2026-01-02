import { useMutation, useQuery } from '@tanstack/react-query';

import { completeSsoCallback, fetchSsoProviders, startSsoLogin } from '@/lib/api/sso';
import type { SsoCallbackInput, SsoStartInput } from '@/lib/api/sso';
import type { TenantSelector } from '@/lib/auth/sso';
import { queryKeys } from '@/lib/queries/keys';

export function useSsoProvidersQuery(selector: TenantSelector | null) {
  return useQuery({
    queryKey: queryKeys.sso.providers(selector ?? null),
    queryFn: () => fetchSsoProviders(selector as TenantSelector),
    enabled: Boolean(selector),
    staleTime: 30 * 1000,
  });
}

export function useStartSsoMutation() {
  return useMutation({
    mutationFn: (input: SsoStartInput) => startSsoLogin(input),
  });
}

export function useCompleteSsoMutation() {
  return useMutation({
    mutationFn: (input: SsoCallbackInput) => completeSsoCallback(input),
  });
}
