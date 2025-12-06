import type { Container } from './types';

export const mockContainers: Container[] = [
  {
    id: 'ctr-1',
    openai_id: 'ctr-1',
    tenant_id: 'tenant',
    owner_user_id: 'user',
    name: 'Default Container',
    memory_limit: '4g',
    status: 'ready',
    expires_after: null,
    last_active_at: new Date().toISOString(),
    metadata: {},
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
];
