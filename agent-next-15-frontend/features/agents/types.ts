import type { AgentSummary } from '@/types/agents';
import type { ToolRegistry } from '@/types/tools';

export type ToolsByAgentMap = Record<string, string[]>;

export interface ToolRegistrySummary {
  totalTools: number;
  categories: string[];
  toolNames: string[];
}

export interface AgentWorkspaceData {
  agents: AgentSummary[];
  tools: ToolRegistry;
  toolsByAgent: ToolsByAgentMap;
}
