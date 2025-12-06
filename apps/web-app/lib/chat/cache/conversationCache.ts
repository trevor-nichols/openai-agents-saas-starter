import type { QueryClient } from '@tanstack/react-query';
import { fetchConversationHistory } from '@/lib/api/conversations';
import { queryKeys } from '@/lib/queries/keys';
import type { ConversationListItem } from '@/types/conversations';

interface ConversationCacheArgs {
  queryClient: QueryClient;
  resolvedConversationId: string;
  previousConversationId: string | null;
  entry: ConversationListItem;
  setCurrentConversationId: (id: string) => void;
  onConversationAdded?: (entry: ConversationListItem) => void;
  onConversationUpdated?: (entry: ConversationListItem) => void;
}

export async function upsertConversationCaches({
  queryClient,
  resolvedConversationId,
  previousConversationId,
  entry,
  setCurrentConversationId,
  onConversationAdded,
  onConversationUpdated,
}: ConversationCacheArgs): Promise<void> {
  if (!previousConversationId) {
    setCurrentConversationId(resolvedConversationId);
    onConversationAdded?.(entry);
  } else if (resolvedConversationId === previousConversationId) {
    onConversationUpdated?.(entry);
  } else {
    setCurrentConversationId(resolvedConversationId);
    onConversationAdded?.(entry);
  }

  try {
    await queryClient.invalidateQueries({
      queryKey: queryKeys.conversations.detail(resolvedConversationId),
    });
  } catch (error) {
    console.warn('[useChatController] Failed to invalidate conversation detail', error);
  }

  try {
    await queryClient.prefetchQuery({
      queryKey: queryKeys.conversations.detail(resolvedConversationId),
      queryFn: () => fetchConversationHistory(resolvedConversationId),
    });
  } catch (error) {
    console.warn('[useChatController] Failed to prefetch conversation detail', error);
  }
}
