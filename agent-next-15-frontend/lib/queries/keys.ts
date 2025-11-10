/**
 * Centralized query keys for TanStack Query
 *
 * Best practice: Define all query keys in one place for:
 * - Type safety
 * - Easy invalidation
 * - Avoiding key typos
 * - Clear cache structure
 */

export const queryKeys = {
  conversations: {
    all: ['conversations'] as const,
    lists: () => [...queryKeys.conversations.all, 'list'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.conversations.lists(), filters] as const,
    details: () => [...queryKeys.conversations.all, 'detail'] as const,
    detail: (id: string) => [...queryKeys.conversations.details(), id] as const,
  },
  billing: {
    all: ['billing'] as const,
    stream: () => [...queryKeys.billing.all, 'stream'] as const,
  },
} as const;
