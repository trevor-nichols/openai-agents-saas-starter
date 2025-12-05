'use client';

import { useCallback, useEffect, useRef, useState } from 'react';

import type {
  StreamingWorkflowEvent,
  WorkflowRunRequestBody,
  LocationHint,
} from '@/lib/api/client/types.gen';
import { streamWorkflowRun } from '@/lib/api/workflows';
import { mockWorkflowStream } from '@/lib/workflows/mock';
import { USE_API_MOCK } from '@/lib/config';
import type { StreamStatus } from '../constants';

type StreamEventWithMeta = StreamingWorkflowEvent & { receivedAt: string };

type StartRunInput = {
  workflowKey: string;
  message: string;
  shareLocation?: boolean;
  location?: LocationHint | null;
};

type RunSummary = {
  workflowKey: string;
  runId?: string | null;
  message?: string;
};

type Options = {
  onRunCreated?: (runId: string, workflowKey?: string | null) => void;
};

export function useWorkflowRunStream(options?: Options) {
  const [events, setEvents] = useState<StreamEventWithMeta[]>([]);
  const [status, setStatus] = useState<StreamStatus>('idle');
  const [error, setError] = useState<string | null>(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [lastSummary, setLastSummary] = useState<RunSummary | null>(null);
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
      };

      try {
        for await (const evt of streamWorkflowRun(input.workflowKey, body)) {
          if (abortRef.current) break;
          const enriched: StreamEventWithMeta = { ...evt, receivedAt: new Date().toISOString() };
          setEvents((prev) => [...prev, enriched]);
          setStreamStatus((current) => (current === 'connecting' ? 'streaming' : current));
          setLastUpdated(enriched.receivedAt);

          if (!autoSelectedRef.current && evt.workflow_run_id) {
            options?.onRunCreated?.(evt.workflow_run_id, evt.workflow_key ?? input.workflowKey);
            autoSelectedRef.current = true;
          }

          if (evt.kind === 'error') {
            const maybeMessage =
              typeof (evt as { payload?: { message?: string } }).payload?.message === 'string'
                ? (evt as { payload?: { message?: string } }).payload?.message
                : undefined;
            setError(maybeMessage ?? 'Workflow reported an error.');
          }

          setLastSummary((prev) => ({
            workflowKey: prev?.workflowKey ?? input.workflowKey,
            runId: prev?.runId ?? evt.workflow_run_id ?? null,
            message: prev?.message ?? input.message,
          }));

          if (evt.is_terminal) {
            setStreamStatus(evt.kind === 'error' ? 'error' : 'completed');
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
      const enriched: StreamEventWithMeta = { ...evt, receivedAt: new Date().toISOString() };
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
