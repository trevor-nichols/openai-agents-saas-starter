import { useCallback } from 'react';

import { useToast } from '@/components/ui/use-toast';
import {
  useCreatePlatformTenantMutation,
  useDeprovisionPlatformTenantMutation,
  useReactivatePlatformTenantMutation,
  useSuspendPlatformTenantMutation,
  useUpdatePlatformTenantMutation,
} from '@/lib/queries/platformTenants';
import type {
  TenantAccountCreateInput,
  TenantAccountOperatorSummary,
  TenantAccountUpdateInput,
} from '@/types/tenantAccount';

import { TENANT_ACTION_RESULT_COPY } from '../constants';
import type { TenantLifecycleAction } from '../types';

interface TenantLifecycleSubmission {
  action: TenantLifecycleAction;
  tenant: TenantAccountOperatorSummary;
  reason: string;
}

interface UseTenantOpsMutationsResult {
  submitLifecycle: (payload: TenantLifecycleSubmission) => Promise<boolean>;
  createTenant: (payload: TenantAccountCreateInput) => Promise<TenantAccountOperatorSummary | null>;
  updateTenant: (
    tenantId: string,
    payload: TenantAccountUpdateInput,
  ) => Promise<TenantAccountOperatorSummary | null>;
  isSubmittingLifecycle: boolean;
  isSubmitting: boolean;
  isCreating: boolean;
  isUpdating: boolean;
}

export function useTenantOpsMutations(): UseTenantOpsMutationsResult {
  const toast = useToast();
  const suspendMutation = useSuspendPlatformTenantMutation();
  const reactivateMutation = useReactivatePlatformTenantMutation();
  const deprovisionMutation = useDeprovisionPlatformTenantMutation();
  const createMutation = useCreatePlatformTenantMutation();
  const updateMutation = useUpdatePlatformTenantMutation();

  const isSubmittingLifecycle =
    suspendMutation.isPending || reactivateMutation.isPending || deprovisionMutation.isPending;
  const isSubmitting = isSubmittingLifecycle || createMutation.isPending || updateMutation.isPending;

  const submitLifecycle = useCallback(
    async ({ action, tenant, reason }: TenantLifecycleSubmission) => {
      try {
        if (action === 'suspend') {
          await suspendMutation.mutateAsync({ tenantId: tenant.id, payload: { reason } });
        } else if (action === 'reactivate') {
          await reactivateMutation.mutateAsync({ tenantId: tenant.id, payload: { reason } });
        } else {
          await deprovisionMutation.mutateAsync({ tenantId: tenant.id, payload: { reason } });
        }
        toast.success({
          title: 'Tenant updated',
          description: `${tenant.name} is now ${TENANT_ACTION_RESULT_COPY[action]}.`,
        });
        return true;
      } catch (err) {
        toast.error({
          title: 'Unable to update tenant',
          description: err instanceof Error ? err.message : 'Try again shortly.',
        });
        return false;
      }
    },
    [deprovisionMutation, reactivateMutation, suspendMutation, toast],
  );

  const createTenant = useCallback(
    async (payload: TenantAccountCreateInput) => {
      try {
        const created = await createMutation.mutateAsync({
          name: payload.name,
          slug: payload.slug ?? undefined,
        });
        toast.success({
          title: 'Tenant created',
          description: `${created.name} is ready for provisioning.`,
        });
        return created;
      } catch (err) {
        toast.error({
          title: 'Unable to create tenant',
          description: err instanceof Error ? err.message : 'Try again shortly.',
        });
        return null;
      }
    },
    [createMutation, toast],
  );

  const updateTenant = useCallback(
    async (tenantId: string, payload: TenantAccountUpdateInput) => {
      try {
        const updated = await updateMutation.mutateAsync({ tenantId, payload });
        toast.success({
          title: 'Tenant updated',
          description: `${updated.name} details were saved.`,
        });
        return updated;
      } catch (err) {
        toast.error({
          title: 'Unable to update tenant',
          description: err instanceof Error ? err.message : 'Try again shortly.',
        });
        return null;
      }
    },
    [toast, updateMutation],
  );

  return {
    submitLifecycle,
    createTenant,
    updateTenant,
    isSubmittingLifecycle,
    isSubmitting,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
  };
}
