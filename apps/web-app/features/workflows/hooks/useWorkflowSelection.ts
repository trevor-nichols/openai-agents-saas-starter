'use client';

import { useCallback, useMemo, useEffect } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

export function useWorkflowSelection(workflowKeys: string[]) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  const selectedWorkflowFromUrl = searchParams.get('workflow');
  const selectedRunFromUrl = searchParams.get('run');

  const initialKey = useMemo(() => workflowKeys[0] ?? null, [workflowKeys]);
  const selectedWorkflowKey = selectedWorkflowFromUrl ?? initialKey ?? null;
  const selectedRunId = selectedRunFromUrl ?? null;

  const updateUrl = useCallback(
    (updates: { workflow?: string | null; run?: string | null }) => {
      const params = new URLSearchParams(searchParams);
      if (updates.workflow !== undefined) {
        if (updates.workflow) params.set('workflow', updates.workflow);
        else params.delete('workflow');
      }
      if (updates.run !== undefined) {
        if (updates.run) params.set('run', updates.run);
        else params.delete('run');
      }
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    },
    [pathname, router, searchParams],
  );

  // ensure URL carries a workflow once list loads
  useEffect(() => {
    if (!selectedWorkflowFromUrl && initialKey) {
      updateUrl({ workflow: initialKey, run: null });
    }
  }, [initialKey, selectedWorkflowFromUrl, updateUrl]);

  const setWorkflow = useCallback(
    (workflowKey: string) => {
      updateUrl({ workflow: workflowKey, run: null });
    },
    [updateUrl],
  );

  const setRun = useCallback(
    (runId: string | null, workflowKey?: string | null) => {
      const targetWorkflow = workflowKey ?? selectedWorkflowKey;
      updateUrl({ workflow: targetWorkflow, run: runId });
    },
    [selectedWorkflowKey, updateUrl],
  );

  const resetRun = useCallback(() => updateUrl({ run: null }), [updateUrl]);

  return {
    selectedWorkflowKey,
    selectedRunId,
    setWorkflow,
    setRun,
    resetRun,
  };
}
