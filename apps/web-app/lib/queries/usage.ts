import { useQuery } from '@tanstack/react-query';

import { listUsageRequest } from '@/lib/api/usage';

export function useUsageQuery(options?: {
  tenantId?: string | null;
  tenantRole?: string | null;
  enabled?: boolean;
}) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ['usage', options?.tenantId ?? 'default'],
    queryFn: () =>
      listUsageRequest({
        tenantId: options?.tenantId,
        tenantRole: options?.tenantRole,
      }),
    enabled,
    staleTime: 60 * 1000,
  });
}
