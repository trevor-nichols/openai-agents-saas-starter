import type {
  StreamingWorkflowEvent,
  WorkflowContext,
} from '@/lib/api/client/types.gen';
import type { GeneratedImageFrame } from '@/lib/streams/imageFrames';

type TextParts = Map<number, string>;

type ToolState = {
  label: string;
  state: 'input-streaming' | 'input-available' | 'output-available' | 'output-error';
  input?: unknown;
  output?: unknown;
  errorText?: string | null;
};

export type WorkflowLiveTranscriptItem =
  | {
      kind: 'message';
      itemId: string;
      outputIndex: number;
      text: string;
      isDone: boolean;
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
      tool: ToolState;
    };

export type WorkflowLiveTranscriptSegment = {
  key: string;
  responseId: string | null;
  agent: string | null;
  workflow: WorkflowContext | null;
  reasoningSummaryText: string | null;
  items: WorkflowLiveTranscriptItem[];
};

type SegmentState = {
  key: string;
  responseId: string | null;
  agent: string | null;
  workflow: WorkflowContext | null;
  reasoningSummaryText: string;
  itemOrder: { itemId: string; outputIndex: number }[];
  itemMeta: Map<
    string,
    { itemType?: string | null; role?: string | null; status?: string | null; done?: boolean }
  >;
  messageTextByItemId: Map<string, TextParts>;
  refusalTextByItemId: Map<string, TextParts>;
  toolByItemId: Map<string, ToolState>;
  toolArgsTextById: Map<string, string>;
  toolCodeById: Map<string, string>;
  imageMetaByToolId: Map<string, { format?: string | null; revisedPrompt?: string | null }>;
  imageFramesByToolId: Map<string, Map<number, GeneratedImageFrame>>;
  chunkAccumulators: Map<string, { encoding: 'base64' | 'utf8' | undefined; parts: Map<number, string> }>;
};

function assembledText(parts: TextParts | undefined): string {
  if (!parts || parts.size === 0) return '';
  return Array.from(parts.entries())
    .sort(([a], [b]) => a - b)
    .map(([, value]) => value)
    .join('');
}

function appendDelta(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; delta: string },
): string {
  const { itemId, contentIndex, delta } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  const existing = parts.get(contentIndex) ?? '';
  parts.set(contentIndex, `${existing}${delta}`);
  store.set(itemId, parts);
  return assembledText(parts);
}

function replaceText(
  store: Map<string, TextParts>,
  update: { itemId: string; contentIndex: number; text: string },
): string {
  const { itemId, contentIndex, text } = update;
  const parts = store.get(itemId) ?? new Map<number, string>();
  parts.set(contentIndex, text);
  store.set(itemId, parts);
  return assembledText(parts);
}

function toolStateFromStatus(status: string): ToolState['state'] {
  if (status === 'completed') return 'output-available';
  if (status === 'failed') return 'output-error';
  return 'input-available';
}

function mimeFromImageFormat(format: string | null | undefined): string {
  if (!format) return 'image/png';
  const normalized = format.toLowerCase();
  if (normalized.includes('png')) return 'image/png';
  if (normalized.includes('jpg') || normalized.includes('jpeg')) return 'image/jpeg';
  if (normalized.includes('webp')) return 'image/webp';
  return `image/${normalized}`;
}

function chunkKeyFor(target: {
  entity_kind: string;
  entity_id: string;
  field: string;
  part_index?: number | null;
}): string {
  return `${target.entity_kind}:${target.entity_id}:${target.field}:${target.part_index ?? ''}`;
}

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

function upsertTool(segment: SegmentState, itemId: string, patch: Partial<ToolState>) {
  const existing =
    segment.toolByItemId.get(itemId) ??
    ({
      label: patch.label ?? 'tool',
      state: 'input-streaming',
      errorText: null,
    } satisfies ToolState);

  const next: ToolState = {
    ...existing,
    ...patch,
    label: patch.label ?? existing.label,
    state: patch.state ?? existing.state,
    input: patch.input ?? existing.input,
    output: patch.output ?? existing.output,
    errorText: patch.errorText ?? existing.errorText,
  };
  segment.toolByItemId.set(itemId, next);
}

function updateToolImageFrames(segment: SegmentState, toolId: string) {
  const framesMap = segment.imageFramesByToolId.get(toolId);
  if (!framesMap) return;
  const frames = Array.from(framesMap.entries())
    .sort(([a], [b]) => a - b)
    .map(([, frame]) => frame);
  if (frames.length === 0) return;
  upsertTool(segment, toolId, { output: frames, label: 'image_generation' });
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
      itemOrder: [],
      itemMeta: new Map(),
      messageTextByItemId: new Map(),
      refusalTextByItemId: new Map(),
      toolByItemId: new Map(),
      toolArgsTextById: new Map(),
      toolCodeById: new Map(),
      imageMetaByToolId: new Map(),
      imageFramesByToolId: new Map(),
      chunkAccumulators: new Map(),
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

    if ('output_index' in event && 'item_id' in event && typeof event.output_index === 'number') {
      ensureItemOrder(segment, { itemId: event.item_id, outputIndex: event.output_index });
    }

    if (kind === 'output_item.added' || kind === 'output_item.done') {
      const meta = segment.itemMeta.get(event.item_id) ?? {};
      meta.itemType = event.item_type;
      meta.role = event.role ?? null;
      meta.status = event.status ?? null;
      meta.done = kind === 'output_item.done';
      segment.itemMeta.set(event.item_id, meta);
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
      segment.reasoningSummaryText += event.delta;
      continue;
    }

    if (kind === 'tool.status') {
      const tool = event.tool;
      const itemId = event.item_id;

      if (tool.tool_type === 'web_search') {
        upsertTool(segment, itemId, {
          label: 'web_search',
          state: toolStateFromStatus(tool.status),
          input: tool.query ?? undefined,
          output: tool.sources ?? undefined,
        });
        continue;
      }

      if (tool.tool_type === 'file_search') {
        upsertTool(segment, itemId, {
          label: 'file_search',
          state: toolStateFromStatus(tool.status),
          input: tool.queries ?? undefined,
          output: tool.results ?? undefined,
        });
        continue;
      }

      if (tool.tool_type === 'code_interpreter') {
        const code = segment.toolCodeById.get(itemId);
        upsertTool(segment, itemId, {
          label: 'code_interpreter',
          state: toolStateFromStatus(tool.status),
          input: code ?? undefined,
          output: tool.container_id || tool.container_mode
            ? { container_id: tool.container_id ?? null, container_mode: tool.container_mode ?? null }
            : undefined,
        });
        continue;
      }

      if (tool.tool_type === 'image_generation') {
        segment.imageMetaByToolId.set(itemId, {
          format: tool.format ?? null,
          revisedPrompt: tool.revised_prompt ?? null,
        });
        upsertTool(segment, itemId, {
          label: 'image_generation',
          state: toolStateFromStatus(tool.status),
          input: tool.revised_prompt ?? undefined,
        });
        updateToolImageFrames(segment, itemId);
        continue;
      }

      if (tool.tool_type === 'function') {
        const argsText = tool.arguments_text ?? segment.toolArgsTextById.get(itemId);
        upsertTool(segment, itemId, {
          label: tool.name,
          state: toolStateFromStatus(tool.status),
          input:
            argsText || tool.arguments_json
              ? {
                  tool_type: 'function',
                  tool_name: tool.name,
                  arguments_text: argsText ?? undefined,
                  arguments_json: tool.arguments_json ?? undefined,
                }
              : undefined,
          output: tool.output ?? undefined,
          errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
        });
        continue;
      }

      // MCP
      const argsText = tool.arguments_text ?? segment.toolArgsTextById.get(itemId);
      upsertTool(segment, itemId, {
        label: tool.tool_name,
        state: toolStateFromStatus(tool.status),
        input:
          argsText || tool.arguments_json
            ? {
                tool_type: 'mcp',
                tool_name: tool.tool_name,
                server_label: tool.server_label ?? null,
                arguments_text: argsText ?? undefined,
                arguments_json: tool.arguments_json ?? undefined,
              }
            : undefined,
        output: tool.output ?? undefined,
        errorText: tool.status === 'failed' ? 'Tool failed' : undefined,
      });
      continue;
    }

    if (kind === 'tool.arguments.delta') {
      const existing = segment.toolArgsTextById.get(event.item_id) ?? '';
      const next = `${existing}${event.delta}`;
      segment.toolArgsTextById.set(event.item_id, next);
      upsertTool(segment, event.item_id, {
        label: event.tool_name,
        state: 'input-streaming',
        input: { tool_type: event.tool_type, tool_name: event.tool_name, arguments_text: next },
      });
      continue;
    }

    if (kind === 'tool.arguments.done') {
      segment.toolArgsTextById.set(event.item_id, event.arguments_text);
      upsertTool(segment, event.item_id, {
        label: event.tool_name,
        state: 'input-available',
        input: {
          tool_type: event.tool_type,
          tool_name: event.tool_name,
          arguments_text: event.arguments_text,
          arguments_json: event.arguments_json ?? undefined,
        },
      });
      continue;
    }

    if (kind === 'tool.code.delta') {
      const existing = segment.toolCodeById.get(event.item_id) ?? '';
      const next = `${existing}${event.delta}`;
      segment.toolCodeById.set(event.item_id, next);
      upsertTool(segment, event.item_id, {
        label: 'code_interpreter',
        state: 'input-streaming',
        input: next,
      });
      continue;
    }

    if (kind === 'tool.code.done') {
      segment.toolCodeById.set(event.item_id, event.code);
      upsertTool(segment, event.item_id, {
        label: 'code_interpreter',
        state: 'input-available',
        input: event.code,
      });
      continue;
    }

    if (kind === 'tool.output') {
      upsertTool(segment, event.item_id, {
        state: 'output-available',
        output: event.output,
      });
      continue;
    }

    if (kind === 'chunk.delta') {
      const key = chunkKeyFor(event.target);
      const existing = segment.chunkAccumulators.get(key) ?? {
        encoding: event.encoding,
        parts: new Map<number, string>(),
      };
      if (!existing.encoding) existing.encoding = event.encoding;
      existing.parts.set(event.chunk_index, event.data);
      segment.chunkAccumulators.set(key, existing);
      continue;
    }

    if (kind === 'chunk.done') {
      const key = chunkKeyFor(event.target);
      const acc = segment.chunkAccumulators.get(key);
      if (!acc) continue;
      segment.chunkAccumulators.delete(key);

      const assembled = Array.from(acc.parts.entries())
        .sort(([a], [b]) => a - b)
        .map(([, value]) => value)
        .join('');

      if (
        event.target.entity_kind === 'tool_call' &&
        event.target.field === 'partial_image_b64' &&
        typeof event.target.part_index === 'number'
      ) {
        const toolId = event.target.entity_id;
        const partIndex = event.target.part_index;
        const meta = segment.imageMetaByToolId.get(toolId);
        const mime = mimeFromImageFormat(meta?.format ?? null);
        const src = acc.encoding === 'base64' ? `data:${mime};base64,${assembled}` : assembled;

        const frames = segment.imageFramesByToolId.get(toolId) ?? new Map<number, GeneratedImageFrame>();
        frames.set(partIndex, {
          id: `${toolId}:${partIndex}`,
          src,
          status: 'partial_image',
          outputIndex: partIndex,
          revisedPrompt: meta?.revisedPrompt ?? undefined,
        });
        segment.imageFramesByToolId.set(toolId, frames);
        updateToolImageFrames(segment, toolId);
      }
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
      const tool = seg.toolByItemId.get(entry.itemId);

      if (tool) {
        items.push({
          kind: 'tool',
          itemId: entry.itemId,
          outputIndex: entry.outputIndex,
          tool,
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
        });
        continue;
      }
    }

    if (items.length === 0 && seg.reasoningSummaryText.length === 0) continue;

    out.push({
      key: seg.key,
      responseId: seg.responseId,
      agent: seg.agent,
      workflow: seg.workflow,
      reasoningSummaryText: seg.reasoningSummaryText.length ? seg.reasoningSummaryText : null,
      items,
    });
  }

  return out;
}
