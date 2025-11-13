import type { AgentSummary } from '@/types/agents';
import type { ToolRegistry } from '@/types/tools';
import type { ToolRegistrySummary, ToolsByAgentMap } from '../types';

function toRecord(registry: ToolRegistry): Record<string, unknown> {
  return (registry ?? {}) as Record<string, unknown>;
}

export function summarizeToolRegistry(registry: ToolRegistry): ToolRegistrySummary {
  const record = toRecord(registry);
  const categories = Array.isArray(record.categories) ? (record.categories as string[]) : [];
  const toolNames = Array.isArray(record.tool_names) ? (record.tool_names as string[]) : [];
  const totalToolsRaw = typeof record.total_tools === 'number' ? (record.total_tools as number) : toolNames.length;

  return {
    totalTools: totalToolsRaw,
    categories,
    toolNames,
  };
}

export function buildToolsByAgentMap(agents: AgentSummary[], registry: ToolRegistry): ToolsByAgentMap {
  const record = toRecord(registry);
  const fallbackToolNames = summarizeToolRegistry(registry).toolNames;

  return agents.reduce<ToolsByAgentMap>((acc, agent) => {
    const entry = record[agent.name];
    if (Array.isArray(entry)) {
      acc[agent.name] = entry as string[];
    } else if (entry && typeof entry === 'object') {
      const nestedList = Array.isArray((entry as Record<string, unknown>).tool_names)
        ? ((entry as Record<string, unknown>).tool_names as string[])
        : [];
      acc[agent.name] = nestedList.length ? nestedList : fallbackToolNames;
    } else {
      acc[agent.name] = fallbackToolNames;
    }
    return acc;
  }, {} as ToolsByAgentMap);
}

export function formatToolingSummary(summary: ToolRegistrySummary): string {
  if (!summary.totalTools) {
    return 'No shared tools registered';
  }
  const suffix = summary.totalTools === 1 ? '' : 's';
  return `${summary.totalTools} tool${suffix} available`;
}
