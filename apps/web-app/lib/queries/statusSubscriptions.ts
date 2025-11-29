import { useMutation } from '@tanstack/react-query';

import {
  createStatusSubscription,
  type CreateStatusSubscriptionInput,
} from '@/lib/api/statusSubscriptions';

export function useStatusSubscriptionMutation() {
  return useMutation({
    mutationFn: (payload: CreateStatusSubscriptionInput) => createStatusSubscription(payload),
  });
}
