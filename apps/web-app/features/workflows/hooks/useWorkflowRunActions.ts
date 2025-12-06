'use client';

import { useCallback, useState } from 'react';

import { useCancelWorkflowRunMutation, useDeleteWorkflowRunMutation } from '@/lib/queries/workflows';
import { useToast } from '@/components/ui/use-toast';

export function useWorkflowRunActions(options: {
  selectedRunId: string | null;
  onRunDeselected?: () => void;
  onAfterDelete?: () => Promise<void> | void;
}) {
  const cancelMutation = useCancelWorkflowRunMutation();
  const deleteMutation = useDeleteWorkflowRunMutation();
  const toast = useToast();
  const [deletingRunId, setDeletingRunId] = useState<string | null>(null);

  const cancelRun = useCallback(() => {
    if (!options.selectedRunId) return;
    cancelMutation.mutate(options.selectedRunId);
  }, [cancelMutation, options.selectedRunId]);

  const deleteRun = useCallback(
    async (runId: string, conversationId?: string | null) => {
      setDeletingRunId(runId);
      const wasSelected = options.selectedRunId === runId;
      try {
        await deleteMutation.mutateAsync({ runId, conversationId });
        if (wasSelected) {
          options.onRunDeselected?.();
        }
        await options.onAfterDelete?.();
        toast.success({ title: 'Run deleted' });
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to delete run';
        toast.error({ title: 'Delete failed', description: message });
      } finally {
        setDeletingRunId((current) => (current === runId ? null : current));
      }
    },
    [deleteMutation, options, toast],
  );

  return {
    cancelRun,
    deleteRun,
    deletingRunId,
    cancelPending: cancelMutation.isPending,
  };
}
