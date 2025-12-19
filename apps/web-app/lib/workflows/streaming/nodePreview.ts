import type { StreamingWorkflowEvent } from '@/lib/api/client/types.gen';
import { assembledText, appendDelta, replaceText, type TextParts } from '@/lib/streams/publicSseV1/textParts';

export type WorkflowNodeToolPreviewStatus = 'waiting' | 'running' | 'done' | 'error';

export type WorkflowNodePreviewItem =
  | Readonly<{
      kind: 'message';
      itemId: string;
      outputIndex: number;
      text: string;
      isDone: boolean;
    }>
  | Readonly<{
      kind: 'refusal';
      itemId: string;
      outputIndex: number;
      text: string;
      isDone: boolean;
    }>
  | Readonly<{
      kind: 'tool';
      itemId: string;
      outputIndex: number;
      label: string;
      status: WorkflowNodeToolPreviewStatus;
      inputPreview: string | null;
    }>;

export type WorkflowNodePreviewSnapshot = Readonly<{
  hasContent: boolean;
  lastUpdatedAt: string | null;
  lifecycleStatus: string | null;
  items: WorkflowNodePreviewItem[];
  overflowCount: number;
}>;

export type WorkflowNodePreviewConfig = Readonly<{
  maxPreviewItems: number;
  maxRetainedItems: number;
  maxTextChars: number;
  maxToolInputChars: number;
}>;

type ItemMeta = {
  itemType?: string | null;
  done: boolean;
};

type ToolState = {
  label: string;
  status: WorkflowNodeToolPreviewStatus;
  inputPreview: string | null;
};

export type WorkflowNodeAccumulator = {
  itemOrder: { itemId: string; outputIndex: number }[];
  itemMeta: Map<string, ItemMeta>;
  messageTextByItemId: Map<string, TextParts>;
  refusalTextByItemId: Map<string, TextParts>;
  toolByItemId: Map<string, ToolState>;
  lifecycleStatus: string | null;
  lastUpdatedAt: string | null;
  dirty: boolean;
};

export function createWorkflowNodeAccumulator(): WorkflowNodeAccumulator {
  return {
    itemOrder: [],
    itemMeta: new Map(),
    messageTextByItemId: new Map(),
    refusalTextByItemId: new Map(),
    toolByItemId: new Map(),
    lifecycleStatus: null,
    lastUpdatedAt: null,
    dirty: false,
  };
}

function truncateText(text: string, maxChars: number): string {
  if (maxChars <= 0) return '';
  if (text.length <= maxChars) return text;
  if (maxChars === 1) return '…';
  return `${text.slice(0, maxChars - 1)}…`;
}

function toolPlaceholderNameFromItemType(itemType: string | undefined | null): string | null {
  if (!itemType) return null;
  if (itemType === 'web_search_call') return 'web_search';
  if (itemType === 'file_search_call') return 'file_search';
  if (itemType === 'code_interpreter_call') return 'code_interpreter';
  if (itemType === 'image_generation_call') return 'image_generation';
  if (itemType === 'mcp_call') return 'mcp';
  if (itemType === 'function_call' || itemType === 'custom_tool_call') return 'function';
  return null;
}

function ensureItemOrder(state: WorkflowNodeAccumulator, update: { itemId: string; outputIndex: number }): void {
  const { itemId, outputIndex } = update;
  const existingMeta = state.itemMeta.get(itemId);
  if (existingMeta) {
    const existing = state.itemOrder.find((entry) => entry.itemId === itemId);
    if (existing && existing.outputIndex !== outputIndex) existing.outputIndex = outputIndex;
    return;
  }

  state.itemMeta.set(itemId, { done: false });
  const insertAt = state.itemOrder.findIndex((entry) => entry.outputIndex > outputIndex);
  if (insertAt === -1) state.itemOrder.push({ itemId, outputIndex });
  else state.itemOrder.splice(insertAt, 0, { itemId, outputIndex });
}

function pruneToRetention(state: WorkflowNodeAccumulator, config: WorkflowNodePreviewConfig): void {
  if (state.itemOrder.length <= config.maxRetainedItems) return;

  const ordered = [...state.itemOrder].sort((a, b) => a.outputIndex - b.outputIndex);
  const keep = ordered.slice(Math.max(0, ordered.length - config.maxRetainedItems));
  const keepIds = new Set(keep.map((entry) => entry.itemId));

  state.itemOrder = keep;
  for (const itemId of Array.from(state.itemMeta.keys())) {
    if (!keepIds.has(itemId)) state.itemMeta.delete(itemId);
  }
  for (const itemId of Array.from(state.messageTextByItemId.keys())) {
    if (!keepIds.has(itemId)) state.messageTextByItemId.delete(itemId);
  }
  for (const itemId of Array.from(state.refusalTextByItemId.keys())) {
    if (!keepIds.has(itemId)) state.refusalTextByItemId.delete(itemId);
  }
  for (const itemId of Array.from(state.toolByItemId.keys())) {
    if (!keepIds.has(itemId)) state.toolByItemId.delete(itemId);
  }
}

function markUpdated(state: WorkflowNodeAccumulator, event: { server_timestamp?: string | null }): void {
  state.lastUpdatedAt = event.server_timestamp ?? new Date().toISOString();
  state.dirty = true;
}

function upsertTool(state: WorkflowNodeAccumulator, itemId: string, patch: Partial<ToolState>): void {
  const existing = state.toolByItemId.get(itemId) ?? { label: 'tool', status: 'running', inputPreview: null };
  state.toolByItemId.set(itemId, {
    label: patch.label ?? existing.label,
    status: patch.status ?? existing.status,
    inputPreview: patch.inputPreview ?? existing.inputPreview,
  });
}

function statusFromTool(tool: Extract<NonNullable<Extract<StreamingWorkflowEvent, { kind: 'tool.status' }>['tool']>, { tool_type: string }>): WorkflowNodeToolPreviewStatus {
  const statusValue = (tool as any).status as string | undefined;
  if (!statusValue) return 'running';
  if (statusValue === 'awaiting_approval') return 'waiting';
  if (statusValue === 'failed') return 'error';
  if (statusValue === 'completed') return 'done';
  return 'running';
}

function labelFromTool(tool: Extract<NonNullable<Extract<StreamingWorkflowEvent, { kind: 'tool.status' }>['tool']>, { tool_type: string }>): string {
  if (tool.tool_type === 'function') return (tool as any).name ?? 'function';
  if (tool.tool_type === 'mcp') return `mcp:${(tool as any).tool_name ?? 'call'}`;
  return tool.tool_type;
}

function inputPreviewFromTool(tool: Extract<NonNullable<Extract<StreamingWorkflowEvent, { kind: 'tool.status' }>['tool']>, { tool_type: string }>): string | null {
  if (tool.tool_type === 'web_search') return (tool as any).query ?? null;
  if (tool.tool_type === 'file_search') {
    const queries = (tool as any).queries as string[] | null | undefined;
    return queries?.[0] ?? null;
  }
  if (tool.tool_type === 'function') return (tool as any).arguments_text ?? null;
  if (tool.tool_type === 'mcp') return (tool as any).arguments_text ?? null;
  return null;
}

export function applyWorkflowEventToNodePreview(
  state: WorkflowNodeAccumulator,
  event: StreamingWorkflowEvent,
  config: WorkflowNodePreviewConfig,
): void {
  const kind = event.kind;
  if (!kind) return;

  if (
    'output_index' in event &&
    typeof (event as any).output_index === 'number' &&
    'item_id' in event &&
    typeof (event as any).item_id === 'string'
  ) {
    ensureItemOrder(state, { itemId: (event as any).item_id, outputIndex: (event as any).output_index });
  }

  if (kind === 'lifecycle') {
    state.lifecycleStatus = event.status ?? null;
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'output_item.added' || kind === 'output_item.done') {
    const meta = state.itemMeta.get(event.item_id) ?? { done: false };
    meta.itemType = event.item_type ?? null;
    meta.done = kind === 'output_item.done';
    state.itemMeta.set(event.item_id, meta);

    if (kind === 'output_item.added') {
      const placeholder = toolPlaceholderNameFromItemType(event.item_type);
      if (placeholder) {
        upsertTool(state, event.item_id, { label: placeholder, status: 'running' });
      }
    }

    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'message.delta') {
    appendDelta(state.messageTextByItemId, {
      itemId: event.item_id,
      contentIndex: event.content_index,
      delta: event.delta,
    });
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'refusal.delta') {
    appendDelta(state.refusalTextByItemId, {
      itemId: event.item_id,
      contentIndex: event.content_index,
      delta: event.delta,
    });
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'refusal.done') {
    replaceText(state.refusalTextByItemId, {
      itemId: event.item_id,
      contentIndex: event.content_index,
      text: event.refusal_text,
    });
    const meta = state.itemMeta.get(event.item_id) ?? { done: false };
    meta.done = true;
    state.itemMeta.set(event.item_id, meta);
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'tool.arguments.delta') {
    const existing = state.toolByItemId.get(event.item_id);
    const nextText = `${existing?.inputPreview ?? ''}${event.delta}`;
    upsertTool(state, event.item_id, {
      label: event.tool_type === 'mcp' ? `mcp:${event.tool_name}` : event.tool_name,
      status: 'running',
      inputPreview: truncateText(nextText, config.maxToolInputChars),
    });
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'tool.arguments.done') {
    const argumentsText = event.arguments_text ?? null;
    upsertTool(state, event.item_id, {
      label: event.tool_type === 'mcp' ? `mcp:${event.tool_name}` : event.tool_name,
      status: 'running',
      inputPreview: argumentsText ? truncateText(argumentsText, config.maxToolInputChars) : null,
    });
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }

  if (kind === 'tool.status') {
    const tool = event.tool as any;
    upsertTool(state, event.item_id, {
      label: labelFromTool(tool),
      status: statusFromTool(tool),
      inputPreview: truncateText(inputPreviewFromTool(tool) ?? state.toolByItemId.get(event.item_id)?.inputPreview ?? '', config.maxToolInputChars) || null,
    });
    markUpdated(state, event);
    pruneToRetention(state, config);
    return;
  }
}

export function buildWorkflowNodePreviewSnapshot(
  state: WorkflowNodeAccumulator,
  config: WorkflowNodePreviewConfig,
): WorkflowNodePreviewSnapshot {
  const ordered = [...state.itemOrder].sort((a, b) => a.outputIndex - b.outputIndex);
  const overflowCount = Math.max(0, ordered.length - config.maxPreviewItems);
  const visible = overflowCount > 0 ? ordered.slice(ordered.length - config.maxPreviewItems) : ordered;

  const items: WorkflowNodePreviewItem[] = [];
  for (const entry of visible) {
    const meta = state.itemMeta.get(entry.itemId) ?? { done: false };
    const done = Boolean(meta.done);

    const tool = state.toolByItemId.get(entry.itemId);
    if (tool) {
      items.push({
        kind: 'tool',
        itemId: entry.itemId,
        outputIndex: entry.outputIndex,
        label: truncateText(tool.label, 42),
        status: tool.status,
        inputPreview: tool.inputPreview ? truncateText(tool.inputPreview, config.maxToolInputChars) : null,
      });
      continue;
    }

    const refusalText = assembledText(state.refusalTextByItemId.get(entry.itemId));
    if (refusalText) {
      const text = done ? refusalText : `${refusalText}▋`;
      items.push({
        kind: 'refusal',
        itemId: entry.itemId,
        outputIndex: entry.outputIndex,
        text: truncateText(text, config.maxTextChars),
        isDone: done,
      });
      continue;
    }

    const messageText = assembledText(state.messageTextByItemId.get(entry.itemId));
    if (messageText) {
      const text = done ? messageText : `${messageText}▋`;
      items.push({
        kind: 'message',
        itemId: entry.itemId,
        outputIndex: entry.outputIndex,
        text: truncateText(text, config.maxTextChars),
        isDone: done,
      });
    }
  }

  return {
    hasContent: items.length > 0 || Boolean(state.lifecycleStatus),
    lastUpdatedAt: state.lastUpdatedAt,
    lifecycleStatus: state.lifecycleStatus,
    items,
    overflowCount,
  };
}

