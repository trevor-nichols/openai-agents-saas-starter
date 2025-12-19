import { useMutation, useQuery } from '@tanstack/react-query';

import {
  listNotificationPreferencesRequest,
  upsertNotificationPreferenceRequest,
} from '@/lib/api/notificationPreferences';
import type { NotificationPreferenceRequest } from '@/lib/api/client/types.gen';

export function useNotificationPreferencesQuery(options?: {
  tenantId?: string | null;
  tenantRole?: string | null;
  enabled?: boolean;
}) {
  const { enabled = true } = options ?? {};
  return useQuery({
    queryKey: ['notification-preferences', options?.tenantId ?? 'default'],
    queryFn: () =>
      listNotificationPreferencesRequest({
        tenantId: options?.tenantId,
        tenantRole: options?.tenantRole,
      }),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useUpsertNotificationPreferenceMutation(options?: {
  tenantId?: string | null;
  tenantRole?: string | null;
}) {
  return useMutation({
    mutationFn: (payload: NotificationPreferenceRequest) =>
      upsertNotificationPreferenceRequest(payload, {
        tenantId: options?.tenantId,
        tenantRole: options?.tenantRole,
      }),
  });
}
