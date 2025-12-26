import type {
  StreamingWorkflowEvent,
  WorkflowContext,
} from '@/lib/api/client/types.gen';
import { assembledText, appendDelta, replaceText, type TextParts } from '@/lib/streams/publicSseV1/textParts';
import { applyReasoningEvent, createReasoningPartsState, getReasoningParts, type ReasoningPart } from '@/lib/streams/publicSseV1/reasoningParts';
import { applyCitationEvent, createCitationsState, getCitationsForItem } from '@/lib/streams/publicSseV1/citations';
import { createAgentToolStreamAccumulator, type AgentToolStream } from '@/lib/streams/publicSseV1/agentToolStreams';
import { asPublicSseEvent, createPublicSseToolAccumulator, type PublicSseToolState } from '@/lib/streams/publicSseV1/tools';
import type { Annotation } from '@/lib/chat/types';

type WorkflowLifecycle = { status: string; reason: string | null };
type WorkflowAgentUpdate = { fromAgent: string | null; toAgent: string; handoffIndex: number | null };
type WorkflowMemoryCheckpoint = { checkpoint: unknown; timestamp: string | null; id: string };

export type WorkflowLiveTranscriptItem =
  | {
      kind: 'message';
      itemId: string;
      outputIndex: number;
      text: string;
      isDone: boolean;
      citations: Annotation[] | null;
    }
  | {
      kind: 'refusal';
      itemId: string;
      outputIndex: number;
      text: string;
      isDone: boolean;
    }
  | {
      kind: 'tool';
      itemId: string;
      outputIndex: number;
      tool: PublicSseToolState;
      agentStream?: AgentToolStream | null;
    };

export type WorkflowLiveTranscriptSegment = {
  key: string;
  responseId: string | null;
  agent: string | null;
  workflow: WorkflowContext | null;
  reasoningSummaryText: string | null;
  reasoningParts: ReasoningPart[] | null;
  lifecycle: WorkflowLifecycle | null;
  agentUpdates: WorkflowAgentUpdate[];
  memoryCheckpoints: WorkflowMemoryCheckpoint[];
  items: WorkflowLiveTranscriptItem[];
};

type SegmentState = {
  key: string;
  responseId: string | null;
  agent: string | null;
  workflow: WorkflowContext | null;
  reasoningSummaryText: string; // legacy single-string view; derived from reasoningParts.
  reasoningParts: ReturnType<typeof createReasoningPartsState>;
  citations: ReturnType<typeof createCitationsState>;
  toolAccumulator: ReturnType<typeof createPublicSseToolAccumulator>;
  agentToolStreams: ReturnType<typeof createAgentToolStreamAccumulator>;
  lifecycle: WorkflowLifecycle | null;
  agentUpdates: WorkflowAgentUpdate[];
  memoryCheckpoints: WorkflowMemoryCheckpoint[];
  itemOrder: { itemId: string; outputIndex: number }[];
  itemMeta: Map<
    string,
    { itemType?: string | null; role?: string | null; status?: string | null; done?: boolean }
  >;
  messageTextByItemId: Map<string, TextParts>;
  refusalTextByItemId: Map<string, TextParts>;
};

function ensureItemOrder(
  segment: SegmentState,
  update: { itemId: string; outputIndex: number },
): void {
  const { itemId, outputIndex } = update;
  if (segment.itemMeta.has(itemId)) {
    const existing = segment.itemOrder.find((entry) => entry.itemId === itemId);
    if (existing && existing.outputIndex !== outputIndex) existing.outputIndex = outputIndex;
    return;
  }
  segment.itemMeta.set(itemId, {});
  const insertAt = segment.itemOrder.findIndex((entry) => entry.outputIndex > outputIndex);
  if (insertAt === -1) segment.itemOrder.push({ itemId, outputIndex });
  else segment.itemOrder.splice(insertAt, 0, { itemId, outputIndex });
}

export function buildWorkflowLiveTranscript(
  events: StreamingWorkflowEvent[],
): WorkflowLiveTranscriptSegment[] {
  const segments = new Map<string, SegmentState>();
  const segmentOrder: string[] = [];
  let unknownCounter = 0;

  const ensureSegment = (event: StreamingWorkflowEvent): SegmentState => {
    const responseId = event.response_id ?? null;
    const key = responseId ?? `unknown-${unknownCounter++}`;
    const existing = segments.get(key);
    if (existing) {
      if (event.agent) existing.agent = event.agent;
      if (event.workflow) existing.workflow = event.workflow;
      return existing;
    }
    const created: SegmentState = {
      key,
      responseId,
      agent: event.agent ?? null,
      workflow: event.workflow ?? null,
      reasoningSummaryText: '',
      reasoningParts: createReasoningPartsState(),
      citations: createCitationsState(),
      toolAccumulator: createPublicSseToolAccumulator(),
      agentToolStreams: createAgentToolStreamAccumulator(),
      lifecycle: null,
      agentUpdates: [],
      memoryCheckpoints: [],
      itemOrder: [],
      itemMeta: new Map(),
      messageTextByItemId: new Map(),
      refusalTextByItemId: new Map(),
    };
    segments.set(key, created);
    segmentOrder.push(key);
    return created;
  };

  for (const event of events) {
    const kind = event.kind;
    if (!kind) continue;

    if (kind === 'final' || kind === 'error') {
      continue;
    }

    const segment = ensureSegment(event);
    const asPublic = asPublicSseEvent(event);

    if (event.scope?.type === 'agent_tool') {
      segment.agentToolStreams.apply(asPublic);
      continue;
    }

    if ('output_index' in event && 'item_id' in event && typeof event.output_index === 'number') {
      ensureItemOrder(segment, { itemId: event.item_id, outputIndex: event.output_index });
    }

    if (kind === 'lifecycle') {
      segment.lifecycle = { status: event.status, reason: event.reason ?? null };
      continue;
    }

    if (kind === 'memory.checkpoint') {
      segment.memoryCheckpoints.push({
        id: `memory-checkpoint-${event.stream_id}-${event.event_id}`,
        checkpoint: event.checkpoint,
        timestamp: event.server_timestamp ?? null,
      });
      continue;
    }

    if (kind === 'agent.updated') {
      segment.agentUpdates.push({
        fromAgent: event.from_agent ?? null,
        toAgent: event.to_agent,
        handoffIndex: typeof event.handoff_index === 'number' ? event.handoff_index : null,
      });
      continue;
    }

    if (kind === 'output_item.added' || kind === 'output_item.done') {
      const meta = segment.itemMeta.get(event.item_id) ?? {};
      meta.itemType = event.item_type;
      meta.role = event.role ?? null;
      meta.status = event.status ?? null;
      meta.done = kind === 'output_item.done';
      segment.itemMeta.set(event.item_id, meta);
      if (kind === 'output_item.added') {
        segment.toolAccumulator.apply(asPublic);
      }
      continue;
    }

    if (kind === 'message.delta') {
      appendDelta(segment.messageTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      continue;
    }

    if (kind === 'message.citation') {
      applyCitationEvent(segment.citations, asPublic);
      continue;
    }

    if (kind === 'refusal.delta') {
      appendDelta(segment.refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        delta: event.delta,
      });
      continue;
    }

    if (kind === 'refusal.done') {
      replaceText(segment.refusalTextByItemId, {
        itemId: event.item_id,
        contentIndex: event.content_index,
        text: event.refusal_text,
      });
      const meta = segment.itemMeta.get(event.item_id) ?? {};
      meta.done = true;
      segment.itemMeta.set(event.item_id, meta);
      continue;
    }

    if (kind === 'reasoning_summary.delta') {
      applyReasoningEvent(segment.reasoningParts, asPublic);
      const parts = getReasoningParts(segment.reasoningParts);
      segment.reasoningSummaryText = parts.map((part) => part.text).join('');
      continue;
    }

    if (
      kind === 'tool.status' ||
      kind === 'tool.arguments.delta' ||
      kind === 'tool.arguments.done' ||
      kind === 'tool.code.delta' ||
      kind === 'tool.code.done' ||
      kind === 'tool.output' ||
      kind === 'tool.approval' ||
      kind === 'chunk.delta' ||
      kind === 'chunk.done'
    ) {
      segment.toolAccumulator.apply(asPublic);
      continue;
    }

    if (kind === 'reasoning_summary.part.added' || kind === 'reasoning_summary.part.done') {
      applyReasoningEvent(segment.reasoningParts, asPublic);
      const parts = getReasoningParts(segment.reasoningParts);
      segment.reasoningSummaryText = parts.map((part) => part.text).join('');
      continue;
    }
  }

  const out: WorkflowLiveTranscriptSegment[] = [];
  for (const key of segmentOrder) {
    const seg = segments.get(key);
    if (!seg) continue;

    const items: WorkflowLiveTranscriptItem[] = [];
    const ordered = [...seg.itemOrder].sort((a, b) => a.outputIndex - b.outputIndex);
    for (const entry of ordered) {
      const meta = seg.itemMeta.get(entry.itemId) ?? {};
      const done = Boolean(meta.done);
      const messageText = assembledText(seg.messageTextByItemId.get(entry.itemId));
      const refusalText = assembledText(seg.refusalTextByItemId.get(entry.itemId));
      const tool = seg.toolAccumulator.getToolById(entry.itemId);

      if (tool) {
        const agentStream = seg.agentToolStreams.getStream(tool.id);
        items.push({
          kind: 'tool',
          itemId: entry.itemId,
          outputIndex: entry.outputIndex,
          tool,
          agentStream,
        });
        continue;
      }

      if (refusalText) {
        items.push({
          kind: 'refusal',
          itemId: entry.itemId,
          outputIndex: entry.outputIndex,
          text: done ? refusalText : `${refusalText}▋`,
          isDone: done,
        });
        continue;
      }

      if (messageText) {
        items.push({
          kind: 'message',
          itemId: entry.itemId,
          outputIndex: entry.outputIndex,
          text: done ? messageText : `${messageText}▋`,
          isDone: done,
          citations: getCitationsForItem(seg.citations, entry.itemId),
        });
        continue;
      }
    }

    const reasoningParts = getReasoningParts(seg.reasoningParts);
    const hasReasoning = reasoningParts.length > 0 || seg.reasoningSummaryText.length > 0;
    if (items.length === 0 && !hasReasoning && seg.agentUpdates.length === 0 && seg.memoryCheckpoints.length === 0) continue;

    out.push({
      key: seg.key,
      responseId: seg.responseId,
      agent: seg.agent,
      workflow: seg.workflow,
      reasoningSummaryText: seg.reasoningSummaryText.length ? seg.reasoningSummaryText : null,
      reasoningParts: reasoningParts.length ? reasoningParts : null,
      lifecycle: seg.lifecycle,
      agentUpdates: seg.agentUpdates,
      memoryCheckpoints: seg.memoryCheckpoints,
      items,
    });
  }

  return out;
}
