'use client';

import { useEffect, useMemo, useRef } from 'react';

import type { StreamingWorkflowEvent, WorkflowDescriptorResponse } from '@/lib/api/client/types.gen';
import { createWorkflowNodeStreamStore, type WorkflowNodeStreamStore } from '@/lib/workflows/streaming';

export function useWorkflowNodeStreamStore(params: {
  descriptor: WorkflowDescriptorResponse | null;
  events: readonly StreamingWorkflowEvent[];
}): WorkflowNodeStreamStore | null {
  const descriptor = params.descriptor;

  const store = useMemo(() => {
    if (!descriptor) return null;
    return createWorkflowNodeStreamStore({ descriptor });
  }, [descriptor]);

  const appliedRef = useRef(0);

  useEffect(() => {
    appliedRef.current = 0;
    store?.reset();
    return () => store?.destroy();
  }, [store]);

  useEffect(() => {
    if (!store) return;

    // If the upstream list resets (new run), reset the store and replay from start.
    if (params.events.length < appliedRef.current) {
      appliedRef.current = 0;
      store.reset();
    }

    const slice = params.events.slice(appliedRef.current);
    if (slice.length) store.applyEvents(slice);
    appliedRef.current = params.events.length;
  }, [params.events, store]);

  return store;
}
