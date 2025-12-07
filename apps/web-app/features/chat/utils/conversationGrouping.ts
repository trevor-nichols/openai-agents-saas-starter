import type { ConversationListItem, ConversationSearchResultItem } from '@/types/conversations';

export type DateGroup = 'Today' | 'Yesterday' | 'Previous 7 Days' | 'Previous 30 Days' | 'Older';

export const DATE_GROUP_ORDER: DateGroup[] = ['Today', 'Yesterday', 'Previous 7 Days', 'Previous 30 Days', 'Older'];

function getGroupForDate(dateStr: string, now: Date): DateGroup {
  const date = new Date(dateStr);
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays <= 1 && now.getDate() === date.getDate()) return 'Today';
  if (diffDays <= 2) return 'Yesterday';
  if (diffDays <= 7) return 'Previous 7 Days';
  if (diffDays <= 30) return 'Previous 30 Days';
  return 'Older';
}

/**
 * Group conversations into labeled date buckets. Accepts an optional clock for testability.
 */
export function groupConversationsByDate(
  conversations: ConversationListItem[],
  now: Date = new Date(),
): Record<DateGroup, ConversationListItem[]> {
  return conversations.reduce<Record<DateGroup, ConversationListItem[]>>((groups, conversation) => {
    const group = getGroupForDate(conversation.updated_at, now);
    if (!groups[group]) groups[group] = [];
    groups[group].push(conversation);
    return groups;
  }, {} as Record<DateGroup, ConversationListItem[]>);
}

/**
 * Normalize search results to the sidebar list item shape.
 */
export function mapSearchResultsToListItems(results: ConversationSearchResultItem[]): ConversationListItem[] {
  return results.map((hit) => ({
    id: hit.conversation_id,
    display_name: hit.display_name ?? null,
    display_name_pending: hit.display_name_pending ?? false,
    title: hit.display_name ?? hit.topic_hint ?? hit.preview,
    topic_hint: hit.topic_hint ?? undefined,
    agent_entrypoint: hit.agent_entrypoint,
    active_agent: hit.active_agent,
    last_message_preview: hit.last_message_preview ?? hit.preview,
    updated_at: hit.updated_at ?? new Date().toISOString(),
  }));
}
