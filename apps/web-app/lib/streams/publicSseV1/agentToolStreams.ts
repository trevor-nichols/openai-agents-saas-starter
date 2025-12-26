import type { PublicSseEvent, StreamScope } from '@/lib/api/client/types.gen';
import type { Annotation } from '@/lib/chat/types';
import {
  appendDelta,
  assembledText,
  replaceText,
  type TextParts,
} from '@/lib/streams/publicSseV1/textParts';
import {
  applyCitationEvent,
  createCitationsState,
  getCitationsForItem,
} from '@/lib/streams/publicSseV1/citations';

export type AgentToolStreamItem = {
  itemId: string;
  outputIndex: number;
  text: string;
  isDone: boolean;
};

export type AgentToolStream = {
  toolCallId: string;
  toolName?: string | null;
  agent?: string | null;
  text: string;
  items: AgentToolStreamItem[];
  isStreaming: boolean;
  citations: Annotation[] | null;
  lastUpdatedAt: string | null;
};

export type AgentToolStreamMap = Record<string, AgentToolStream>;

type StreamState = {
  toolCallId: string;
  toolName?: string | null;
  agent?: string | null;
  itemOrder: { itemId: string; outputIndex: number }[];
  itemMeta: Map<string, { done?: boolean }>;
  messageTextByItemId: Map<string, TextParts>;
  refusalTextByItemId: Map<string, TextParts>;
  citations: ReturnType<typeof createCitationsState>;
  lastUpdatedAt: string | null;
};

type AccumulatorParams = {
  onStreams?: (streams: AgentToolStreamMap) => void;
};

const isAgentToolScope = (scope: StreamScope | null | undefined): scope is StreamScope =>
  Boolean(scope && scope.type === 'agent_tool' && scope.tool_call_id);

const ensureItemOrder = (
  state: StreamState,
  update: { itemId: string; outputIndex: number },
) => {
  const { itemId, outputIndex } = update;
  if (state.itemMeta.has(itemId)) {
    const existing = state.itemOrder.find((entry) => entry.itemId === itemId);
    if (existing && existing.outputIndex !== outputIndex) existing.outputIndex = outputIndex;
    return;
  }
  state.itemMeta.set(itemId, {});
  const insertAt = state.itemOrder.findIndex((entry) => entry.outputIndex > outputIndex);
  if (insertAt === -1) state.itemOrder.push({ itemId, outputIndex });
  else state.itemOrder.splice(insertAt, 0, { itemId, outputIndex });
};

const buildStream = (state: StreamState): AgentToolStream | null => {
  const ordered = [...state.itemOrder].sort((a, b) => a.outputIndex - b.outputIndex);
  const items: AgentToolStreamItem[] = [];

  for (const entry of ordered) {
    const messageText = assembledText(state.messageTextByItemId.get(entry.itemId));
    const refusalText = assembledText(state.refusalTextByItemId.get(entry.itemId));
    const text = refusalText || messageText;
    if (!text) continue;
    const meta = state.itemMeta.get(entry.itemId);
    items.push({
      itemId: entry.itemId,
      outputIndex: entry.outputIndex,
      text,
      isDone: Boolean(meta?.done),
    });
  }

  if (items.length === 0) return null;

  const text = items.map((item) => item.text).join('\n\n');
  const isStreaming = items.some((item) => !item.isDone);
  const citations =
    items.length === 1 ? getCitationsForItem(state.citations, items[0]?.itemId ?? '') : null;

  return {
    toolCallId: state.toolCallId,
    toolName: state.toolName ?? null,
    agent: state.agent ?? null,
    text,
    items,
    isStreaming,
    citations,
    lastUpdatedAt: state.lastUpdatedAt ?? null,
  };
};

export type AgentToolStreamAccumulator = {
  apply: (event: PublicSseEvent) => void;
  getStreams: () => AgentToolStream[];
  getStreamsByToolCallId: () => AgentToolStreamMap;
  getStream: (toolCallId: string) => AgentToolStream | null;
};

export function createAgentToolStreamAccumulator(
  params: AccumulatorParams = {},
): AgentToolStreamAccumulator {
  const streamByToolCallId = new Map<string, StreamState>();

  const getStreamState = (scope: StreamScope, timestamp?: string | null) => {
    const existing = streamByToolCallId.get(scope.tool_call_id);
    if (existing) {
      if (scope.tool_name && !existing.toolName) existing.toolName = scope.tool_name;
      if (scope.agent && !existing.agent) existing.agent = scope.agent;
      if (timestamp) existing.lastUpdatedAt = timestamp;
      return existing;
    }

    const created: StreamState = {
      toolCallId: scope.tool_call_id,
      toolName: scope.tool_name ?? null,
      agent: scope.agent ?? null,
      itemOrder: [],
      itemMeta: new Map(),
      messageTextByItemId: new Map(),
      refusalTextByItemId: new Map(),
      citations: createCitationsState(),
      lastUpdatedAt: timestamp ?? null,
    };
    streamByToolCallId.set(scope.tool_call_id, created);
    return created;
  };

  const emit = () => {
    params.onStreams?.(getStreamsByToolCallId());
  };

  const apply = (event: PublicSseEvent) => {
    const scope = event.scope;
    if (!isAgentToolScope(scope)) return;

    const state = getStreamState(scope, event.server_timestamp ?? null);

    if (event.kind === 'output_item.added' || event.kind === 'output_item.done') {
      ensureItemOrder(state, { itemId: event.item_id, outputIndex: event.output_index });
      if (event.kind === 'output_item.done') {
        const meta = state.itemMeta.get(event.item_id) ?? {};
        meta.done = true;
        state.itemMeta.set(event.item_id, meta);
      }
      emit();
      return;
    }

    if (event.kind === 'message.delta') {
      ensureItemOrder(state, { itemId: event.item_id, outputIndex: event.output_index });
      appendDelta(state.messageTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      emit();
      return;
    }

    if (event.kind === 'message.citation') {
      applyCitationEvent(state.citations, event);
      emit();
      return;
    }

    if (event.kind === 'refusal.delta') {
      ensureItemOrder(state, { itemId: event.item_id, outputIndex: event.output_index });
      appendDelta(state.refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      emit();
      return;
    }

    if (event.kind === 'refusal.done') {
      ensureItemOrder(state, { itemId: event.item_id, outputIndex: event.output_index });
      replaceText(state.refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        text: event.refusal_text,
      });
      const meta = state.itemMeta.get(event.item_id) ?? {};
      meta.done = true;
      state.itemMeta.set(event.item_id, meta);
      emit();
    }
  };

  const getStreams = (): AgentToolStream[] => {
    const out: AgentToolStream[] = [];
    for (const state of streamByToolCallId.values()) {
      const stream = buildStream(state);
      if (stream) out.push(stream);
    }
    return out;
  };

  const getStreamsByToolCallId = (): AgentToolStreamMap => {
    const out: AgentToolStreamMap = {};
    for (const state of streamByToolCallId.values()) {
      const stream = buildStream(state);
      if (!stream) continue;
      out[state.toolCallId] = stream;
    }
    return out;
  };

  const getStream = (toolCallId: string): AgentToolStream | null => {
    const state = streamByToolCallId.get(toolCallId);
    if (!state) return null;
    return buildStream(state);
  };

  return { apply, getStreams, getStreamsByToolCallId, getStream };
}
