import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import { createPublicSseToolAccumulator } from '@/lib/streams/publicSseV1/tools';
import { parseTimestampMs } from '@/lib/utils/time';

import type { ChatMessage, ToolEventAnchors, ToolState } from '../types';

type ToolTimeline = {
  tools: ToolState[];
  anchors: ToolEventAnchors;
};

type MessageTimeIndex = {
  id: string;
  timestampMs: number;
};

const buildMessageTimeIndex = (messages: ChatMessage[]): MessageTimeIndex[] =>
  messages
    .filter((message) => message.kind !== 'memory_checkpoint')
    .map((message) => {
      const timestampMs = parseTimestampMs(message.timestamp ?? null);
      if (timestampMs === null) return null;
      return { id: message.id, timestampMs };
    })
    .filter((entry): entry is MessageTimeIndex => Boolean(entry))
    .sort((a, b) => a.timestampMs - b.timestampMs);

const findAnchorMessageId = (messageIndex: MessageTimeIndex[], toolTimestampMs: number): string | null => {
  if (messageIndex.length === 0) return null;
  const first = messageIndex[0];
  if (!first) return null;
  if (toolTimestampMs < first.timestampMs) return null;

  let low = 0;
  let high = messageIndex.length - 1;
  while (low <= high) {
    const mid = Math.floor((low + high) / 2);
    const entry = messageIndex[mid];
    if (!entry) break;
    if (entry.timestampMs === toolTimestampMs) {
      return entry.id;
    }
    if (entry.timestampMs < toolTimestampMs) {
      low = mid + 1;
    } else {
      high = mid - 1;
    }
  }

  const resolved = messageIndex[Math.max(0, high)];
  return resolved?.id ?? null;
};

export function extractMemoryCheckpointMarkers(events: PublicSseEvent[]): ChatMessage[] {
  const markers: ChatMessage[] = [];
  for (const event of events) {
    if (event.kind !== 'memory.checkpoint') continue;
    const streamId = event.stream_id;
    const eventId = event.event_id;
    markers.push({
      id: `memory-checkpoint-${streamId}-${eventId}`,
      role: 'assistant',
      kind: 'memory_checkpoint',
      content: '',
      timestamp: event.server_timestamp ?? undefined,
      checkpoint: event.checkpoint,
    });
  }
  return markers;
}

export function mapLedgerEventsToToolTimeline(events: PublicSseEvent[], messages: ChatMessage[]): ToolTimeline {
  if (events.length === 0 || messages.length === 0) {
    return { tools: [], anchors: {} };
  }

  const toolAccumulator = createPublicSseToolAccumulator();
  for (const event of events) {
    toolAccumulator.apply(event);
  }

  const orderedTools = (toolAccumulator.getToolsSorted() as unknown as ToolState[]).sort((a, b) => {
    const aMs = toolAccumulator.getFirstSeenMs(a.id) ?? Number.POSITIVE_INFINITY;
    const bMs = toolAccumulator.getFirstSeenMs(b.id) ?? Number.POSITIVE_INFINITY;
    if (aMs !== bMs) return aMs - bMs;
    return (a.outputIndex ?? Number.POSITIVE_INFINITY) - (b.outputIndex ?? Number.POSITIVE_INFINITY);
  });

  const messageIndex = buildMessageTimeIndex(messages);
  const anchors: ToolEventAnchors = {};
  for (const tool of orderedTools) {
    const ts = toolAccumulator.getFirstSeenMs(tool.id);
    if (ts === null) continue;
    const anchorId = findAnchorMessageId(messageIndex, ts);
    if (!anchorId) continue;
    anchors[anchorId] = [...(anchors[anchorId] ?? []), tool.id];
  }

  return { tools: orderedTools, anchors };
}
