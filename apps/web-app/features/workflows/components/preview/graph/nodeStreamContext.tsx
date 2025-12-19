'use client';

import { createContext, useCallback, useContext, useSyncExternalStore, type ReactNode } from 'react';

import type { WorkflowNodePreviewSnapshot, WorkflowNodeStreamStore } from '@/lib/workflows/streaming';

const EMPTY_SNAPSHOT: WorkflowNodePreviewSnapshot = {
  hasContent: false,
  lastUpdatedAt: null,
  lifecycleStatus: null,
  items: [],
  overflowCount: 0,
};

const WorkflowNodeStreamContext = createContext<WorkflowNodeStreamStore | null>(null);

export function WorkflowNodeStreamProvider({
  store,
  children,
}: {
  store: WorkflowNodeStreamStore | null;
  children: ReactNode;
}) {
  return (
    <WorkflowNodeStreamContext.Provider value={store}>
      {children}
    </WorkflowNodeStreamContext.Provider>
  );
}

export function useWorkflowNodePreview(nodeId: string): WorkflowNodePreviewSnapshot {
  const store = useContext(WorkflowNodeStreamContext);

  const getSnapshot = useCallback(() => store?.getSnapshot(nodeId) ?? EMPTY_SNAPSHOT, [nodeId, store]);
  const subscribe = useCallback(
    (notify: () => void) => store?.subscribe(nodeId, notify) ?? (() => {}),
    [nodeId, store],
  );

  return useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
}
