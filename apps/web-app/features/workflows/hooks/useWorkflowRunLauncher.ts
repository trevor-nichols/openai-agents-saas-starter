'use client';

import { useCallback } from 'react';

import type { WorkflowRunLaunchInput, WorkflowRunStartInput } from '../types';

type Options = {
  startRun: (input: WorkflowRunStartInput) => Promise<void>;
  containerOverrides: Record<string, string | null>;
  vectorStoreOverrides: Record<string, string | null>;
  supportsContainersByAgent: Record<string, boolean>;
  supportsFileSearchByAgent: Record<string, boolean>;
  onAfterRun?: () => void | Promise<void>;
};

export function useWorkflowRunLauncher({
  startRun,
  containerOverrides,
  vectorStoreOverrides,
  supportsContainersByAgent,
  supportsFileSearchByAgent,
  onAfterRun,
}: Options) {
  return useCallback(
    async (input: WorkflowRunLaunchInput) => {
      const resolvedOverridesEntries = Object.entries(containerOverrides).flatMap(
        ([agentKey, containerId]) => {
          if (!containerId) return [];
          if (!supportsContainersByAgent[agentKey]) return [];
          return [[agentKey, containerId] as const];
        },
      );
      const resolvedOverrides = Object.fromEntries(resolvedOverridesEntries);
      const resolvedVectorOverridesEntries = Object.entries(vectorStoreOverrides).flatMap(
        ([agentKey, storeId]) => {
          if (!storeId) return [];
          if (!supportsFileSearchByAgent[agentKey]) return [];
          return [[agentKey, { vector_store_id: storeId }] as const];
        },
      );
      const resolvedVectorOverrides = Object.fromEntries(resolvedVectorOverridesEntries);

      await startRun({
        ...input,
        containerOverrides: Object.keys(resolvedOverrides).length ? resolvedOverrides : undefined,
        vectorStoreOverrides: Object.keys(resolvedVectorOverrides).length ? resolvedVectorOverrides : undefined,
      });

      if (onAfterRun) {
        await onAfterRun();
      }
    },
    [
      containerOverrides,
      onAfterRun,
      startRun,
      supportsContainersByAgent,
      supportsFileSearchByAgent,
      vectorStoreOverrides,
    ],
  );
}
