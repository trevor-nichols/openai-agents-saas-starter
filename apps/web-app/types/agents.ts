import type {
  AgentListResponse as BackendAgentListResponse,
  AgentStatus as BackendAgentStatus,
  AgentSummary as BackendAgentSummary,
} from '@/lib/api/client/types.gen';

export interface AgentSummary extends BackendAgentSummary {
  display_name?: string | null;
  model?: string | null;
  last_seen_at?: string | null;
}

export interface AgentListResponse extends Omit<BackendAgentListResponse, 'items'> {
  items: AgentSummary[];
}

export type AgentStatus = BackendAgentStatus;
