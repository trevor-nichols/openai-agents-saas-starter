import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import {
  createPlatformTenant,
  deprovisionPlatformTenant,
  fetchPlatformTenant,
  fetchPlatformTenants,
  reactivatePlatformTenant,
  suspendPlatformTenant,
  updatePlatformTenant,
} from '@/lib/api/platformTenants';
import type {
  PlatformTenantListFilters,
  TenantAccountCreateInput,
  TenantAccountLifecycleInput,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

import { queryKeys } from './keys';

const DEFAULT_LIMIT = 25;

function normalizeFilters(filters: PlatformTenantListFilters): PlatformTenantListFilters {
  return {
    ...filters,
    limit: filters.limit ?? DEFAULT_LIMIT,
    offset: filters.offset ?? 0,
  };
}

export function usePlatformTenantsQuery(filters: PlatformTenantListFilters = {}) {
  const normalized = normalizeFilters(filters);
  return useQuery({
    queryKey: queryKeys.platformTenants.list(normalized as Record<string, unknown>),
    queryFn: () => fetchPlatformTenants(normalized),
    staleTime: 30 * 1000,
  });
}

export function usePlatformTenantQuery(tenantId: string | null, options?: { enabled?: boolean }) {
  return useQuery({
    queryKey: queryKeys.platformTenants.detail(tenantId ?? 'unknown'),
    queryFn: () => fetchPlatformTenant(tenantId ?? ''),
    enabled: options?.enabled ?? Boolean(tenantId),
    staleTime: 30 * 1000,
  });
}

export function useCreatePlatformTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TenantAccountCreateInput) => createPlatformTenant(payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.platformTenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.platformTenants.all }).catch(() => null);
    },
  });
}

export function useUpdatePlatformTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      payload,
    }: {
      tenantId: string;
      payload: TenantAccountUpdateInput;
    }) => updatePlatformTenant(tenantId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.platformTenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.platformTenants.all }).catch(() => null);
    },
  });
}

export function useSuspendPlatformTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      payload,
    }: {
      tenantId: string;
      payload: TenantAccountLifecycleInput;
    }) => suspendPlatformTenant(tenantId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.platformTenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.platformTenants.all }).catch(() => null);
    },
  });
}

export function useReactivatePlatformTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      payload,
    }: {
      tenantId: string;
      payload: TenantAccountLifecycleInput;
    }) => reactivatePlatformTenant(tenantId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.platformTenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.platformTenants.all }).catch(() => null);
    },
  });
}

export function useDeprovisionPlatformTenantMutation() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      tenantId,
      payload,
    }: {
      tenantId: string;
      payload: TenantAccountLifecycleInput;
    }) => deprovisionPlatformTenant(tenantId, payload),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.platformTenants.detail(data.id), data);
      queryClient.invalidateQueries({ queryKey: queryKeys.platformTenants.all }).catch(() => null);
    },
  });
}
