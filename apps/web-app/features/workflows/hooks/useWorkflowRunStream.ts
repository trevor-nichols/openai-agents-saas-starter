'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import type {
  WorkflowRunRequestBody,
  LocationHint,
} from '@/lib/api/client/types.gen';
import { streamWorkflowRun } from '@/lib/api/workflows';
import { mockWorkflowStream } from '@/lib/workflows/mock';
import { USE_API_MOCK } from '@/lib/config';
import type { StreamStatus } from '../constants';
import type { WorkflowRunSummary, WorkflowStreamEventWithReceivedAt } from '../types';

type StartRunInput = {
  workflowKey: string;
  message: string;
  shareLocation?: boolean;
  location?: LocationHint | null;
  containerOverrides?: Record<string, string> | null;
};

type Options = {
  onRunCreated?: (runId: string, workflowKey?: string | null) => void;
};

export function useWorkflowRunStream(options?: Options) {
  const [events, setEvents] = useState<WorkflowStreamEventWithReceivedAt[]>([]);
  const [status, setStatus] = useState<StreamStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastSummary, setLastSummary] = useState<WorkflowRunSummary | null>(null);
  const [lastUpdated, setLastUpdated] = useState<string | null>(null);

  const abortRef = useRef(false);
  const autoSelectedRef = useRef(false);
  const statusRef = useRef<StreamStatus>('idle');

  const setStreamStatus = useCallback((next: StreamStatus | ((current: StreamStatus) => StreamStatus)) => {
    setStatus((current) => {
      const resolved = typeof next === 'function' ? (next as (c: StreamStatus) => StreamStatus)(current) : next;
      statusRef.current = resolved;
      return resolved;
    });
  }, []);

  useEffect(() => {
    abortRef.current = false;
    autoSelectedRef.current = false;
    statusRef.current = 'idle';
    return () => {
      abortRef.current = true;
    };
  }, []);

  const startRun = useCallback(
    async (input: StartRunInput) => {
      abortRef.current = false;
      autoSelectedRef.current = false;
      setError(null);
      setEvents([]);
      setIsStreaming(true);
      setStreamStatus('connecting');
      setLastSummary({ workflowKey: input.workflowKey, runId: null, message: input.message });
      setLastUpdated(null);

      const body: WorkflowRunRequestBody = {
        message: input.message,
        share_location: input.shareLocation ?? null,
        location: input.shareLocation ? input.location ?? null : null,
        container_overrides: input.containerOverrides ?? null,
      };

      try {
        for await (const evt of streamWorkflowRun(input.workflowKey, body)) {
          if (abortRef.current) break;
          const enriched: WorkflowStreamEventWithReceivedAt = { ...evt, receivedAt: new Date().toISOString() };
          setEvents((prev) => [...prev, enriched]);
          setStreamStatus((current) => (current === 'connecting' ? 'streaming' : current));
          setLastUpdated(enriched.receivedAt);

          const workflowRunId = evt.workflow?.workflow_run_id ?? null;
          const workflowKey = evt.workflow?.workflow_key ?? null;

          if (!autoSelectedRef.current && workflowRunId) {
            options?.onRunCreated?.(workflowRunId, workflowKey ?? input.workflowKey);
            autoSelectedRef.current = true;
          }

          if (evt.kind === 'error') {
            setError(evt.error.message ?? 'Workflow reported an error.');
          }

          setLastSummary((prev) => ({
            workflowKey: prev?.workflowKey ?? workflowKey ?? input.workflowKey,
            runId: prev?.runId ?? workflowRunId ?? null,
            message: prev?.message ?? input.message,
          }));

          if (evt.kind === 'error' || evt.kind === 'final') {
            if (evt.kind === 'final' && evt.final.status !== 'completed') {
              setError(`Workflow finished with status: ${evt.final.status}`);
              setStreamStatus('error');
            } else {
              setStreamStatus(evt.kind === 'error' ? 'error' : 'completed');
            }
            break;
          }
        }
      } catch (err) {
        if (!abortRef.current) {
          setError(err instanceof Error ? err.message : 'Failed to run workflow');
          setStreamStatus('error');
        }
      } finally {
        setIsStreaming(false);
        if (!abortRef.current && statusRef.current === 'connecting') {
          setStreamStatus('error');
        }
      }
    },
    [options, setStreamStatus],
  );

  const simulate = useCallback(async () => {
    if (!USE_API_MOCK) return;
    setError(null);
    setEvents([]);
    const runId = `mock_run_${Date.now()}`;
    for await (const evt of mockWorkflowStream(runId)) {
      const enriched: WorkflowStreamEventWithReceivedAt = { ...evt, receivedAt: new Date().toISOString() };
      setEvents((prev) => [...prev, enriched]);
    }
  }, []);

  const reset = useCallback(() => {
    setEvents([]);
    setError(null);
    setIsStreaming(false);
    setStreamStatus('idle');
    setLastSummary(null);
    setLastUpdated(null);
    abortRef.current = false;
    autoSelectedRef.current = false;
  }, [setStreamStatus]);

  return {
    events,
    status,
    error,
    isStreaming,
    lastSummary,
    lastUpdated,
    startRun,
    simulate,
    reset,
  };
}
