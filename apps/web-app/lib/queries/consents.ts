import { useMutation, useQuery } from '@tanstack/react-query';

import { listConsentsRequest, recordConsentRequest } from '@/lib/api/consents';
import type { ConsentRequest } from '@/lib/api/client/types.gen';

export function useConsentsQuery(enabled = true) {
  return useQuery({
    queryKey: ['consents'],
    queryFn: () => listConsentsRequest(),
    enabled,
    staleTime: 5 * 60 * 1000,
  });
}

export function useRecordConsentMutation() {
  return useMutation({
    mutationFn: (payload: ConsentRequest) => recordConsentRequest(payload),
  });
}
