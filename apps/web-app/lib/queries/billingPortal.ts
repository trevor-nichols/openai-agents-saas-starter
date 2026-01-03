import { useMutation } from '@tanstack/react-query';

import { createBillingPortalSession } from '@/lib/api/billingPortal';
import type { BillingPortalSession, BillingPortalSessionPayload } from '@/lib/types/billing';
import { useFeatureFlags } from '@/lib/queries/featureFlags';

interface PortalOptions {
  tenantId: string | null;
  tenantRole?: string | null;
}

export function useCreatePortalSessionMutation(options: PortalOptions) {
  const { flags } = useFeatureFlags();
  const billingEnabled = Boolean(flags?.billingEnabled);
  const { tenantId, tenantRole = null } = options;

  return useMutation<BillingPortalSession, Error, BillingPortalSessionPayload>({
    mutationFn: async (payload) => {
      if (!billingEnabled) {
        throw new Error('Billing is disabled.');
      }
      if (!tenantId) {
        throw new Error('Tenant id required');
      }
      return createBillingPortalSession(tenantId, payload, { tenantRole });
    },
  });
}
