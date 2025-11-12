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
    plans: () => [...queryKeys.billing.all, 'plans'] as const,
  },
  tools: {
    all: ['tools'] as const,
    list: () => [...queryKeys.tools.all, 'list'] as const,
  },
  agents: {
    all: ['agents'] as const,
    list: () => [...queryKeys.agents.all, 'list'] as const,
    detail: (agentName: string) => [...queryKeys.agents.all, 'detail', agentName] as const,
  },
  account: {
    all: ['account'] as const,
    profile: () => [...queryKeys.account.all, 'profile'] as const,
    sessions: {
      all: () => [...queryKeys.account.all, 'sessions'] as const,
      list: (params: { limit: number; offset: number; tenantId: string | null; includeRevoked: boolean }) =>
        [...queryKeys.account.sessions.all(), params] as const,
    },
    serviceAccounts: {
      all: () => [...queryKeys.account.all, 'service-accounts'] as const,
      list: (filters?: Record<string, unknown>) =>
        [...queryKeys.account.serviceAccounts.all(), filters] as const,
    },
  },
} as const;
