import { useMutation } from '@tanstack/react-query';

import { submitContactRequest } from '@/lib/api/contact';
import type { ContactSubmission } from '@/types/marketing';

export function useSubmitContactMutation() {
  return useMutation<void, Error, ContactSubmission>({
    mutationFn: (payload) => submitContactRequest(payload),
  });
}

