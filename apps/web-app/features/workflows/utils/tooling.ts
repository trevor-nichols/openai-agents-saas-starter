import type { ToolRegistry } from '@/types/tools';

type ToolRegistrySnapshot = {
  toolNames: string[];
  perAgent: Record<string, unknown> | null;
};

export type ResolvedAgentTools = {
  tools: string[];
  isFallback: boolean;
};

function toRecord(registry: ToolRegistry): Record<string, unknown> {
  return (registry ?? {}) as Record<string, unknown>;
}

export function getToolRegistrySnapshot(registry: ToolRegistry): ToolRegistrySnapshot {
  const record = toRecord(registry);
  const toolNames = Array.isArray(record.tool_names) ? (record.tool_names as string[]) : [];
  const perAgent =
    record.per_agent && typeof record.per_agent === 'object'
      ? (record.per_agent as Record<string, unknown>)
      : null;

  return { toolNames, perAgent };
}

function normalizeToolList(list: string[], toolNames: string[]): string[] {
  if (!toolNames.length) {
    return list;
  }
  const allowed = new Set(toolNames);
  return list.filter((tool) => allowed.has(tool));
}

export function resolveAgentTools(
  snapshot: ToolRegistrySnapshot,
  agentKey: string,
): ResolvedAgentTools {
  const { toolNames, perAgent } = snapshot;
  const entry = perAgent?.[agentKey];

  if (Array.isArray(entry)) {
    return {
      tools: normalizeToolList(entry.filter((tool): tool is string => typeof tool === 'string'), toolNames),
      isFallback: false,
    };
  }
  if (typeof entry === 'string') {
    return {
      tools: normalizeToolList([entry], toolNames),
      isFallback: false,
    };
  }
  if (entry && typeof entry === 'object') {
    const nested = (entry as Record<string, unknown>).tool_names;
    if (Array.isArray(nested)) {
      return {
        tools: normalizeToolList(nested.filter((tool): tool is string => typeof tool === 'string'), toolNames),
        isFallback: false,
      };
    }
  }
  if (perAgent && Object.prototype.hasOwnProperty.call(perAgent, agentKey)) {
    return { tools: [], isFallback: false };
  }
  return { tools: toolNames, isFallback: true };
}

export function resolveSupportsContainers(tools: string[]): boolean {
  return tools.includes('code_interpreter');
}

export function resolveSupportsFileSearch(tools: string[]): boolean {
  return tools.includes('file_search');
}
