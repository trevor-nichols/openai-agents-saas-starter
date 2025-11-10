import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AgentChatRequest, AgentChatResponse } from '@/lib/api/client/types.gen';
import { queryKeys } from './keys';

export function useSendChatMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AgentChatRequest) => {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorPayload = (await response.json().catch(() => ({}))) as { message?: string };
        throw new Error(errorPayload.message ?? 'Failed to send chat message');
      }

      return (await response.json()) as AgentChatResponse;
    },
    onSuccess: (response: AgentChatResponse) => {
      if (response.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.detail(response.conversation_id),
        });
        queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.lists(),
        });
      }
    },
  });
}

