'use client';

import { useMemo } from 'react';

import type { WorkflowDescriptor } from '@/lib/workflows/types';
import type { ToolRegistry } from '@/types/tools';
import {
  getToolRegistrySnapshot,
  resolveAgentTools,
  resolveSupportsContainers,
  resolveSupportsFileSearch,
} from '../utils/tooling';

type WorkflowCapabilities = {
  toolsByAgent: Record<string, string[]>;
  supportsContainersByAgent: Record<string, boolean>;
  supportsFileSearchByAgent: Record<string, boolean>;
};

export function useWorkflowCapabilities(
  descriptor: WorkflowDescriptor | null,
  tools: ToolRegistry,
): WorkflowCapabilities {
  const agentKeys = useMemo(() => {
    const keys = new Set<string>();
    descriptor?.stages?.forEach((stage) => {
      stage.steps?.forEach((step) => {
        if (step.agent_key) {
          keys.add(step.agent_key);
        }
      });
    });
    return Array.from(keys);
  }, [descriptor]);

  const toolRegistrySnapshot = useMemo(() => getToolRegistrySnapshot(tools), [tools]);

  const toolsByAgent = useMemo(() => {
    const map: Record<string, string[]> = {};
    agentKeys.forEach((agentKey) => {
      map[agentKey] = resolveAgentTools(toolRegistrySnapshot, agentKey).tools;
    });
    return map;
  }, [agentKeys, toolRegistrySnapshot]);

  const supportsContainersByAgent = useMemo(() => {
    const map: Record<string, boolean> = {};
    agentKeys.forEach((agentKey) => {
      map[agentKey] = resolveSupportsContainers(toolsByAgent[agentKey] ?? []);
    });
    return map;
  }, [agentKeys, toolsByAgent]);

  const supportsFileSearchByAgent = useMemo(() => {
    const map: Record<string, boolean> = {};
    agentKeys.forEach((agentKey) => {
      map[agentKey] = resolveSupportsFileSearch(toolsByAgent[agentKey] ?? []);
    });
    return map;
  }, [agentKeys, toolsByAgent]);

  return { toolsByAgent, supportsContainersByAgent, supportsFileSearchByAgent };
}
