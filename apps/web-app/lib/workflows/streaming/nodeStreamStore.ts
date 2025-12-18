import type { StreamingWorkflowEvent, WorkflowDescriptorResponse } from '@/lib/api/client/types.gen';

import { buildWorkflowDescriptorIndex, resolveWorkflowNodeIdForEvent, type WorkflowDescriptorIndex, type WorkflowGraphNodeId } from './descriptorIndex';
import {
  applyWorkflowEventToNodePreview,
  buildWorkflowNodePreviewSnapshot,
  createWorkflowNodeAccumulator,
  type WorkflowNodeAccumulator,
  type WorkflowNodePreviewConfig,
  type WorkflowNodePreviewSnapshot,
} from './nodePreview';

export type WorkflowNodeStreamStoreScheduler = Readonly<{
  schedule: (cb: () => void) => WorkflowNodeStreamStoreHandle;
  cancel: (handle: WorkflowNodeStreamStoreHandle) => void;
}>;

export type WorkflowNodeStreamStore = Readonly<{
  descriptorKey: string;
  getSnapshot: (nodeId: WorkflowGraphNodeId) => WorkflowNodePreviewSnapshot;
  subscribe: (nodeId: WorkflowGraphNodeId, listener: () => void) => () => void;
  applyEvents: (events: readonly StreamingWorkflowEvent[]) => void;
  reset: () => void;
  destroy: () => void;
}>;

export type WorkflowNodeStreamStoreHandle = number | ReturnType<typeof setTimeout>;

const DEFAULT_CONFIG: WorkflowNodePreviewConfig = {
  maxPreviewItems: 6,
  maxRetainedItems: 24,
  maxTextChars: 600,
  maxToolInputChars: 220,
};

function defaultScheduler(): WorkflowNodeStreamStoreScheduler {
  const schedule = globalThis.requestAnimationFrame
    ? (cb: () => void) => globalThis.requestAnimationFrame(cb)
    : (cb: () => void) => globalThis.setTimeout(cb, 50);
  const cancel = globalThis.cancelAnimationFrame
    ? (handle: WorkflowNodeStreamStoreHandle) => globalThis.cancelAnimationFrame(handle as number)
    : (handle: WorkflowNodeStreamStoreHandle) => globalThis.clearTimeout(handle as ReturnType<typeof setTimeout>);

  return { schedule, cancel };
}

function emptySnapshot(): WorkflowNodePreviewSnapshot {
  return {
    hasContent: false,
    lastUpdatedAt: null,
    lifecycleStatus: null,
    items: [],
    overflowCount: 0,
  };
}

export function createWorkflowNodeStreamStore(params: {
  descriptor: WorkflowDescriptorResponse;
  config?: Partial<WorkflowNodePreviewConfig>;
  scheduler?: WorkflowNodeStreamStoreScheduler;
}): WorkflowNodeStreamStore {
  const config: WorkflowNodePreviewConfig = {
    ...DEFAULT_CONFIG,
    ...(params.config ?? {}),
  };

  const normalizedConfig: WorkflowNodePreviewConfig = {
    ...config,
    maxPreviewItems: Math.max(1, config.maxPreviewItems),
    maxRetainedItems: Math.max(config.maxPreviewItems, config.maxRetainedItems),
    maxTextChars: Math.max(1, config.maxTextChars),
    maxToolInputChars: Math.max(1, config.maxToolInputChars),
  };

  const index: WorkflowDescriptorIndex = buildWorkflowDescriptorIndex(params.descriptor);
  const scheduler = params.scheduler ?? defaultScheduler();

  const accumulators = new Map<WorkflowGraphNodeId, WorkflowNodeAccumulator>();
  const snapshots = new Map<WorkflowGraphNodeId, WorkflowNodePreviewSnapshot>();
  const emptySnapshots = new Map<WorkflowGraphNodeId, WorkflowNodePreviewSnapshot>();

  const listenersByNodeId = new Map<WorkflowGraphNodeId, Set<() => void>>();
  const dirtyNodes = new Set<WorkflowGraphNodeId>();
  let notifyHandle: WorkflowNodeStreamStoreHandle | null = null;
  let destroyed = false;

  const getEmptySnapshotForNode = (nodeId: WorkflowGraphNodeId): WorkflowNodePreviewSnapshot => {
    const existing = emptySnapshots.get(nodeId);
    if (existing) return existing;
    const created = emptySnapshot();
    emptySnapshots.set(nodeId, created);
    return created;
  };

  const getSnapshot = (nodeId: WorkflowGraphNodeId): WorkflowNodePreviewSnapshot => {
    if (destroyed) return getEmptySnapshotForNode(nodeId);
    return snapshots.get(nodeId) ?? getEmptySnapshotForNode(nodeId);
  };

  const subscribe = (nodeId: WorkflowGraphNodeId, listener: () => void) => {
    if (destroyed) return () => {};
    const set = listenersByNodeId.get(nodeId) ?? new Set<() => void>();
    set.add(listener);
    listenersByNodeId.set(nodeId, set);
    return () => {
      const current = listenersByNodeId.get(nodeId);
      if (!current) return;
      current.delete(listener);
      if (current.size === 0) listenersByNodeId.delete(nodeId);
    };
  };

  const flush = () => {
    if (destroyed) return;

    const toNotify = Array.from(dirtyNodes);
    dirtyNodes.clear();

    for (const nodeId of toNotify) {
      const state = accumulators.get(nodeId);
      if (state?.dirty) {
        snapshots.set(nodeId, buildWorkflowNodePreviewSnapshot(state, normalizedConfig));
        state.dirty = false;
      } else if (!snapshots.has(nodeId)) {
        snapshots.set(nodeId, getEmptySnapshotForNode(nodeId));
      }

      const listeners = listenersByNodeId.get(nodeId);
      if (!listeners?.size) continue;
      listeners.forEach((fn) => fn());
    }
  };

  const scheduleFlush = () => {
    if (notifyHandle !== null) return;
    // Use a placeholder so synchronous schedulers don't overwrite the cleared handle.
    notifyHandle = -1 as unknown as WorkflowNodeStreamStoreHandle;
    const handle = scheduler.schedule(() => {
      notifyHandle = null;
      flush();
    });
    if (notifyHandle !== null) notifyHandle = handle;
  };

  const applyEvents = (events: readonly StreamingWorkflowEvent[]) => {
    if (destroyed) return;

    const changedNodes = new Set<WorkflowGraphNodeId>();
    for (const event of events) {
      const nodeId = resolveWorkflowNodeIdForEvent(index, event);
      if (!nodeId) continue;

      const acc = accumulators.get(nodeId) ?? createWorkflowNodeAccumulator();
      applyWorkflowEventToNodePreview(acc, event, normalizedConfig);
      accumulators.set(nodeId, acc);
      changedNodes.add(nodeId);
    }

    if (changedNodes.size === 0) return;
    changedNodes.forEach((nodeId) => dirtyNodes.add(nodeId));
    scheduleFlush();
  };

  const reset = () => {
    if (destroyed) return;
    accumulators.clear();
    snapshots.clear();
    for (const nodeId of index.knownNodeIds) dirtyNodes.add(nodeId);
    scheduleFlush();
  };

  const destroy = () => {
    destroyed = true;
    if (notifyHandle !== null) scheduler.cancel(notifyHandle);
    notifyHandle = null;
    dirtyNodes.clear();
    listenersByNodeId.clear();
    accumulators.clear();
    snapshots.clear();
    emptySnapshots.clear();
  };

  return {
    descriptorKey: params.descriptor.key,
    getSnapshot,
    subscribe,
    applyEvents,
    reset,
    destroy,
  };
}
