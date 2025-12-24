'use client';

import { useCallback, useMemo, useState } from 'react';

type OverridesByWorkflow = Record<string, Record<string, string | null>>;

type WorkflowOverrides = {
  containerOverrides: Record<string, string | null>;
  vectorStoreOverrides: Record<string, string | null>;
  setContainerOverride: (agentKey: string, containerId: string | null) => void;
  setVectorStoreOverride: (agentKey: string, vectorStoreId: string | null) => void;
};

export function useWorkflowOverrides(selectedWorkflowKey?: string | null): WorkflowOverrides {
  const [containerOverridesByWorkflow, setContainerOverridesByWorkflow] = useState<OverridesByWorkflow>({});
  const [vectorStoreOverridesByWorkflow, setVectorStoreOverridesByWorkflow] = useState<OverridesByWorkflow>({});

  const containerOverrides = useMemo(() => {
    if (!selectedWorkflowKey) {
      return {};
    }
    return containerOverridesByWorkflow[selectedWorkflowKey] ?? {};
  }, [containerOverridesByWorkflow, selectedWorkflowKey]);

  const vectorStoreOverrides = useMemo(() => {
    if (!selectedWorkflowKey) {
      return {};
    }
    return vectorStoreOverridesByWorkflow[selectedWorkflowKey] ?? {};
  }, [selectedWorkflowKey, vectorStoreOverridesByWorkflow]);

  const setContainerOverride = useCallback(
    (agentKey: string, containerId: string | null) => {
      if (!selectedWorkflowKey) return;
      setContainerOverridesByWorkflow((prev) => {
        const current = prev[selectedWorkflowKey] ?? {};
        return {
          ...prev,
          [selectedWorkflowKey]: {
            ...current,
            [agentKey]: containerId,
          },
        };
      });
    },
    [selectedWorkflowKey],
  );

  const setVectorStoreOverride = useCallback(
    (agentKey: string, vectorStoreId: string | null) => {
      if (!selectedWorkflowKey) return;
      setVectorStoreOverridesByWorkflow((prev) => {
        const current = prev[selectedWorkflowKey] ?? {};
        return {
          ...prev,
          [selectedWorkflowKey]: {
            ...current,
            [agentKey]: vectorStoreId,
          },
        };
      });
    },
    [selectedWorkflowKey],
  );

  return {
    containerOverrides,
    vectorStoreOverrides,
    setContainerOverride,
    setVectorStoreOverride,
  };
}
