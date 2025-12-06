import { useMutation, useQueryClient } from '@tanstack/react-query';

import type { AgentChatRequest, AgentChatResponse } from '@/lib/api/client/types.gen';
import { ChatApiError, sendChatMessage } from '@/lib/api/chat';
import { queryKeys } from './keys';

export function useSendChatMutation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (payload: AgentChatRequest) => {
      try {
        return await sendChatMessage(payload);
      } catch (error) {
        if (error instanceof ChatApiError) {
          throw error;
        }

        const message = error instanceof Error ? error.message : 'Unknown chat error';
        throw new ChatApiError(message, { status: 500 });
      }
    },
    onSuccess: (response: AgentChatResponse) => {
      if (response.conversation_id) {
        queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.detail(response.conversation_id),
        });
        queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.lists(),
        });
        queryClient.invalidateQueries({
          queryKey: queryKeys.conversations.messages(response.conversation_id),
        });
      }
    },
  });
}
