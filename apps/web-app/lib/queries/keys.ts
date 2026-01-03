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
    messages: (id: string) => [...queryKeys.conversations.all, 'messages', id] as const,
    events: (id: string, filters?: Record<string, unknown>) =>
      [...queryKeys.conversations.all, 'events', id, filters ?? {}] as const,
    ledger: (id: string, filters?: Record<string, unknown>) =>
      [...queryKeys.conversations.all, 'ledger', id, filters ?? {}] as const,
  },
  billing: {
    all: ['billing'] as const,
    stream: () => [...queryKeys.billing.all, 'stream'] as const,
    plans: () => [...queryKeys.billing.all, 'plans'] as const,
    history: (tenantId: string | null, filters?: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'history', tenantId ?? 'unknown', filters] as const,
    subscription: (tenantId: string | null) =>
      [...queryKeys.billing.all, 'subscription', tenantId ?? 'unknown'] as const,
    invoices: (tenantId: string | null, filters?: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'invoices', tenantId ?? 'unknown', filters ?? {}] as const,
    invoice: (tenantId: string | null, invoiceId: string | null) =>
      [...queryKeys.billing.all, 'invoice', tenantId ?? 'unknown', invoiceId ?? 'unknown'] as const,
    usageTotals: (tenantId: string | null, filters?: Record<string, unknown>) =>
      [...queryKeys.billing.all, 'usage-totals', tenantId ?? 'unknown', filters ?? {}] as const,
    paymentMethods: (tenantId: string | null) =>
      [...queryKeys.billing.all, 'payment-methods', tenantId ?? 'unknown'] as const,
    upcomingInvoiceBase: (tenantId: string | null) =>
      [...queryKeys.billing.all, 'upcoming-invoice', tenantId ?? 'unknown'] as const,
    upcomingInvoice: (tenantId: string | null, seatCount?: number | null) =>
      [...queryKeys.billing.upcomingInvoiceBase(tenantId), { seatCount: seatCount ?? null }] as const,
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
  guardrails: {
    all: ['guardrails'] as const,
    list: () => [...queryKeys.guardrails.all, 'list'] as const,
    detail: (guardrailKey: string) => [...queryKeys.guardrails.all, 'detail', guardrailKey] as const,
    presets: {
      all: () => [...queryKeys.guardrails.all, 'presets'] as const,
      list: () => [...queryKeys.guardrails.presets.all(), 'list'] as const,
      detail: (presetKey: string) => [...queryKeys.guardrails.presets.all(), 'detail', presetKey] as const,
    },
  },
  status: {
    all: ['status'] as const,
    snapshot: () => [...queryKeys.status.all, 'snapshot'] as const,
  },
  features: {
    all: ['features'] as const,
    flags: () => [...queryKeys.features.all, 'flags'] as const,
  },
  statusOps: {
    all: ['status-ops'] as const,
    subscriptions: (filters?: Record<string, unknown>) =>
      [...queryKeys.statusOps.all, 'subscriptions', filters ?? {}] as const,
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
  users: {
    all: ['users'] as const,
    profile: () => [...queryKeys.users.all, 'profile'] as const,
  },
  tenant: {
    all: ['tenant'] as const,
    settings: () => [...queryKeys.tenant.all, 'settings'] as const,
    account: () => [...queryKeys.tenant.all, 'account'] as const,
  },
  platformTenants: {
    all: ['platform-tenants'] as const,
    list: (filters?: Record<string, unknown>) =>
      [...queryKeys.platformTenants.all, 'list', filters ?? {}] as const,
    detail: (tenantId: string) =>
      [...queryKeys.platformTenants.all, 'detail', tenantId] as const,
  },
  team: {
    all: ['team'] as const,
    members: {
      all: () => [...queryKeys.team.all, 'members'] as const,
      list: (filters?: Record<string, unknown>) =>
        [...queryKeys.team.members.all(), filters ?? {}] as const,
    },
    invites: {
      all: () => [...queryKeys.team.all, 'invites'] as const,
      list: (filters?: Record<string, unknown>) =>
        [...queryKeys.team.invites.all(), filters ?? {}] as const,
    },
  },
  signup: {
    all: ['signup'] as const,
    policy: () => [...queryKeys.signup.all, 'policy'] as const,
    invites: {
      all: () => [...queryKeys.signup.all, 'invites'] as const,
      list: (filters?: Record<string, unknown>) =>
        [...queryKeys.signup.invites.all(), filters] as const,
    },
    requests: {
      all: () => [...queryKeys.signup.all, 'requests'] as const,
      list: (filters?: Record<string, unknown>) =>
        [...queryKeys.signup.requests.all(), filters] as const,
    },
  },
  sso: {
    all: ['sso'] as const,
    providers: (selector?: Record<string, unknown> | null) =>
      [...queryKeys.sso.all, 'providers', selector ?? {}] as const,
  },
  workflows: {
    all: ['workflows'] as const,
    list: () => [...queryKeys.workflows.all, 'list'] as const,
    run: (runId: string) => [...queryKeys.workflows.all, 'run', runId] as const,
    runReplay: (runId: string | null) =>
      [...queryKeys.workflows.all, 'run-replay', runId ?? 'none'] as const,
    descriptor: (workflowKey: string | null) =>
      [...queryKeys.workflows.all, 'descriptor', workflowKey ?? 'none'] as const,
    runs: (filters?: Record<string, unknown>) =>
      [...queryKeys.workflows.all, 'runs', filters ?? {}] as const,
  },
  storage: {
    all: ['storage'] as const,
    objects: (filters?: Record<string, unknown>) => [...queryKeys.storage.all, 'objects', filters ?? {}] as const,
  },
  assets: {
    all: ['assets'] as const,
    list: (filters?: Record<string, unknown>) => [...queryKeys.assets.all, 'list', filters ?? {}] as const,
    detail: (assetId: string) => [...queryKeys.assets.all, 'detail', assetId] as const,
    thumbnails: (assetIds: string[]) => [...queryKeys.assets.all, 'thumbnails', assetIds] as const,
  },
  vectorStores: {
    all: ['vector-stores'] as const,
    list: () => [...queryKeys.vectorStores.all, 'list'] as const,
    files: (vectorStoreId: string) => [...queryKeys.vectorStores.all, 'files', vectorStoreId] as const,
  },
  containers: {
    all: ['containers'] as const,
    list: () => [...queryKeys.containers.all, 'list'] as const,
  },
  marketing: {
    all: ['marketing'] as const,
    contact: () => [...queryKeys.marketing.all, 'contact'] as const,
  },
  activity: {
    all: ['activity'] as const,
    list: (filters?: Record<string, unknown>) => [...queryKeys.activity.all, 'list', filters ?? {}] as const,
  },
} as const;
