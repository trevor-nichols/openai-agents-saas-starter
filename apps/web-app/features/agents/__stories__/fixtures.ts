import type { ContainerResponse } from '@/lib/api/client/types.gen';
import type { AgentSummary } from '@/types/agents';

import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

const now = Date.now();

export const agentSummaries: AgentSummary[] = [
  {
    name: 'triage_agent',
    display_name: 'Triage Agent',
    description: 'Routes requests and summarizes context.',
    status: 'active',
    model: 'gpt-5.1',
    last_seen_at: new Date(now - 3 * 60 * 1000).toISOString(),
  },
  {
    name: 'research_agent',
    display_name: 'Research Agent',
    description: 'Deep dives across docs and web.',
    status: 'active',
    model: 'gpt-5.1',
    last_seen_at: new Date(now - 45 * 60 * 1000).toISOString(),
  },
  {
    name: 'ops_agent',
    display_name: 'Ops Agent',
    description: 'Handles billing and account automations.',
    status: 'inactive',
    model: 'gpt-4.1',
    last_seen_at: null,
  },
];

export const toolsByAgent: ToolsByAgentMap = {
  triage_agent: ['file_search', 'web_search'],
  research_agent: ['web_search', 'browser', 'code_interpreter'],
  ops_agent: ['billing_ledger'],
};

export const toolsSummary: ToolRegistrySummary = {
  totalTools: 5,
  categories: ['search', 'code_interpreter', 'billing'],
  toolNames: ['file_search', 'web_search', 'browser', 'code_interpreter', 'billing_ledger'],
};

export const sampleContainers: ContainerResponse[] = [
  {
    id: 'ctr-1',
    openai_id: 'ctr_openai_1',
    tenant_id: 'tenant-123',
    owner_user_id: null,
    name: 'gpu-sandbox',
    memory_limit: '8g',
    status: 'ready',
    expires_after: null,
    last_active_at: new Date(now - 60 * 60 * 1000).toISOString(),
    metadata: {},
    created_at: new Date(now - 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(now - 30 * 60 * 1000).toISOString(),
  },
  {
    id: 'ctr-2',
    openai_id: 'ctr_openai_2',
    tenant_id: 'tenant-123',
    owner_user_id: null,
    name: 'cpu-queue',
    memory_limit: '4g',
    status: 'provisioning',
    expires_after: null,
    last_active_at: null,
    metadata: {},
    created_at: new Date(now - 3 * 24 * 60 * 60 * 1000).toISOString(),
    updated_at: new Date(now - 2 * 60 * 60 * 1000).toISOString(),
  },
];
