import type { ConversationEvent } from '@/types/conversations';
import { parseTimestampMs } from '@/lib/utils/time';
import type { AgentToolStreamMap } from '@/lib/streams/publicSseV1/agentToolStreams';
import type { ChatMessage, ToolEventAnchors, ToolState } from '../types';

type ToolTimeline = {
  tools: ToolState[];
  anchors: ToolEventAnchors;
};

const CURSOR_TOKEN = '▋';
const ANCHOR_MATCH_WINDOW_MS = 2 * 60 * 1000;

const normalizeContentForSignature = (content: string): string =>
  content.replace(new RegExp(`${CURSOR_TOKEN}\\s*$`), '').trim();

const messageSignature = (message: ChatMessage): string =>
  `${message.role}:${normalizeContentForSignature(message.content)}`;

const isToolRelated = (event: ConversationEvent): boolean => {
  // Only treat normalized tool/mcp items as tools. Some non-tool items (e.g., reasoning)
  // can still have an `id` and historically leaked into `tool_call_id` at the persistence layer.
  const type = event.run_item_type;
  return type === 'tool_call' || type === 'tool_result' || type === 'mcp_call';
};

const isUserMessageEvent = (event: ConversationEvent): boolean =>
  event.role === 'user' && Boolean(event.content_text && event.content_text.trim().length > 0);

type MessageTimeIndex = {
  id: string;
  timestampMs: number;
};

const buildMessageTimeIndex = (messages: ChatMessage[]): MessageTimeIndex[] =>
  messages
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

export function mapConversationEventsToToolTimeline(
  events: ConversationEvent[],
  messages: ChatMessage[],
): ToolTimeline {
  if (events.length === 0 || messages.length === 0) {
    return { tools: [], anchors: {} };
  }

  const messageIndex = buildMessageTimeIndex(messages);
  const orderedEvents = [...events].sort((a, b) => a.sequence_no - b.sequence_no);
  const userMessages = messages.filter((message) => message.role === 'user');
  const userEvents = orderedEvents.filter(isUserMessageEvent);
  const canAnchorByUserEvents = userMessages.length > 0 && userEvents.length >= userMessages.length;

  const anchorIdByUserSequence = new Map<number, string>();
  if (canAnchorByUserEvents) {
    const start = userEvents.length - userMessages.length;
    for (let i = start; i < userEvents.length; i += 1) {
      const userEvent = userEvents[i];
      const userMessage = userMessages[i - start];
      if (!userEvent || !userMessage) continue;
      anchorIdByUserSequence.set(userEvent.sequence_no, userMessage.id);
    }
  }

  type ToolAggregate = {
    id: string;
    name: string | null;
    firstSeenSequenceNo: number | null;
    firstSeenMs: number | null;
    anchorId: string | null;
    input?: unknown;
    output?: unknown;
  };

  const toolById = new Map<string, ToolAggregate>();
  let currentAnchorId: string | null = null;

  for (const event of orderedEvents) {
    if (canAnchorByUserEvents && isUserMessageEvent(event)) {
      currentAnchorId = anchorIdByUserSequence.get(event.sequence_no) ?? currentAnchorId;
    }

    if (!isToolRelated(event)) continue;

    const toolId = event.tool_call_id?.trim();
    if (!toolId) continue;

    const existing =
      toolById.get(toolId) ??
      ({
        id: toolId,
        name: event.tool_name ?? null,
        firstSeenSequenceNo: null,
        firstSeenMs: null,
        anchorId: null,
      } satisfies ToolAggregate);

    if (existing.firstSeenSequenceNo === null || event.sequence_no < existing.firstSeenSequenceNo) {
      existing.firstSeenSequenceNo = event.sequence_no;
    }

    const seenMs = parseTimestampMs(event.timestamp);
    if (seenMs !== null) {
      if (existing.firstSeenMs === null || seenMs < existing.firstSeenMs) {
        existing.firstSeenMs = seenMs;
      }
    }

    if (!existing.name && event.tool_name) {
      existing.name = event.tool_name;
    }

    if (existing.anchorId === null && currentAnchorId) {
      existing.anchorId = currentAnchorId;
    }

    if (event.call_arguments !== undefined && event.call_arguments !== null) {
      existing.input = event.call_arguments;
    }

    if (event.call_output !== undefined && event.call_output !== null) {
      existing.output = event.call_output;
    }

    toolById.set(toolId, existing);
  }

  const orderedTools = Array.from(toolById.values())
    .filter((tool) => tool.firstSeenSequenceNo !== null)
    .sort((a, b) => (a.firstSeenSequenceNo ?? 0) - (b.firstSeenSequenceNo ?? 0));

  const anchors: ToolEventAnchors = {};
  const anchoredToolIds: string[] = [];

  const canFallbackToTimestamps = !canAnchorByUserEvents && messageIndex.length > 0;

  for (const tool of orderedTools) {
    const anchorId =
      tool.anchorId ??
      (canFallbackToTimestamps && tool.firstSeenMs !== null
        ? findAnchorMessageId(messageIndex, tool.firstSeenMs)
        : null);
    if (!anchorId) continue;

    anchors[anchorId] = [...(anchors[anchorId] ?? []), tool.id];
    anchoredToolIds.push(tool.id);
  }

  const anchoredToolIdSet = new Set(anchoredToolIds);
  const tools: ToolState[] = orderedTools
    .filter((tool) => anchoredToolIdSet.has(tool.id))
    .map((tool) => ({
      id: tool.id,
      name: tool.name,
      status:
        tool.output !== undefined
          ? 'output-available'
          : tool.input !== undefined
            ? 'input-available'
            : 'input-streaming',
      input: tool.input,
      output: tool.output,
      errorText: null,
    }));

  return { tools, anchors };
}

export function mergeToolStates(base: ToolState[], overlay: ToolState[]): ToolState[] {
  if (base.length === 0) return overlay;
  if (overlay.length === 0) return base;

  const statusRank: Record<ToolState['status'], number> = {
    'input-streaming': 0,
    'input-available': 1,
    'output-available': 2,
    'output-error': 3,
  };

  const mergeOne = (existing: ToolState, incoming: ToolState): ToolState => ({
    ...existing,
    ...incoming,
    // Avoid clobbering stable fields with `undefined` from partial updates.
    name: incoming.name ?? existing.name,
    toolType: incoming.toolType ?? existing.toolType,
    agent: incoming.agent ?? existing.agent,
    outputIndex: incoming.outputIndex ?? existing.outputIndex,
    input: incoming.input ?? existing.input,
    output: incoming.output ?? existing.output,
    errorText: incoming.errorText ?? existing.errorText,
    status:
      statusRank[incoming.status] > statusRank[existing.status] ? incoming.status : existing.status,
  });

  const byId = new Map<string, ToolState>();
  base.forEach((tool) => byId.set(tool.id, tool));
  overlay.forEach((tool) => {
    const existing = byId.get(tool.id);
    byId.set(tool.id, existing ? mergeOne(existing, tool) : tool);
  });

  const merged: ToolState[] = [];
  const seen = new Set<string>();
  for (const tool of base) {
    const resolved = byId.get(tool.id);
    if (!resolved || seen.has(resolved.id)) continue;
    merged.push(resolved);
    seen.add(resolved.id);
  }
  for (const tool of overlay) {
    const resolved = byId.get(tool.id);
    if (!resolved || seen.has(resolved.id)) continue;
    merged.push(resolved);
    seen.add(resolved.id);
  }
  return merged;
}

export function mergeToolEventAnchors(
  base: ToolEventAnchors,
  overlay: ToolEventAnchors,
): ToolEventAnchors {
  const baseEntries = Object.entries(base);
  const overlayEntries = Object.entries(overlay);
  if (baseEntries.length === 0) return overlay;
  if (overlayEntries.length === 0) return base;

  const overlayToolIds = new Set<string>();
  for (const [, toolIds] of overlayEntries) {
    for (const toolId of toolIds) {
      if (toolId) overlayToolIds.add(toolId);
    }
  }

  // Prefer overlay anchors when the same tool id appears in both sources. This avoids
  // a tool "jumping" between anchors when persisted events load mid-stream.
  const merged: ToolEventAnchors = {};
  for (const [anchorId, toolIds] of baseEntries) {
    const filtered = toolIds.filter((toolId) => toolId && !overlayToolIds.has(toolId));
    if (filtered.length > 0) {
      merged[anchorId] = filtered;
    }
  }
  for (const [anchorId, toolIds] of overlayEntries) {
    if (toolIds.length === 0) continue;
    const existing = merged[anchorId] ?? [];
    if (existing.length === 0) {
      merged[anchorId] = [...toolIds];
      continue;
    }
    const deduped = new Set(existing);
    const nextIds = [...existing];
    for (const toolId of toolIds) {
      if (deduped.has(toolId)) continue;
      deduped.add(toolId);
      nextIds.push(toolId);
    }
    merged[anchorId] = nextIds;
  }

  return merged;
}

export function mergeAgentToolStreams(
  base: AgentToolStreamMap,
  overlay: AgentToolStreamMap,
): AgentToolStreamMap {
  const baseEntries = Object.entries(base);
  const overlayEntries = Object.entries(overlay);
  if (baseEntries.length === 0) return overlay;
  if (overlayEntries.length === 0) return base;

  const merged: AgentToolStreamMap = { ...base };
  for (const [toolCallId, stream] of overlayEntries) {
    merged[toolCallId] = stream;
  }
  return merged;
}

type AnchorCandidate = {
  id: string;
  timestampMs: number | null;
  index: number;
};

const buildCandidatesBySignature = (messages: ChatMessage[]): Map<string, AnchorCandidate[]> => {
  const bySignature = new Map<string, AnchorCandidate[]>();
  for (const [index, message] of messages.entries()) {
    const timestampMs = parseTimestampMs(message.timestamp ?? null);
    const signature = messageSignature(message);
    const existing = bySignature.get(signature);
    const candidate: AnchorCandidate = { id: message.id, timestampMs, index };
    if (existing) {
      existing.push(candidate);
    } else {
      bySignature.set(signature, [candidate]);
    }
  }

  for (const candidates of bySignature.values()) {
    candidates.sort((a, b) => {
      const aTime = a.timestampMs ?? Number.POSITIVE_INFINITY;
      const bTime = b.timestampMs ?? Number.POSITIVE_INFINITY;
      if (aTime !== bTime) return aTime - bTime;
      return a.index - b.index;
    });
  }

  return bySignature;
};

const findOrdinal = (candidates: AnchorCandidate[], id: string): number | null => {
  const idx = candidates.findIndex((candidate) => candidate.id === id);
  return idx >= 0 ? idx : null;
};

const findClosestCandidateId = (
  candidates: AnchorCandidate[],
  source: { timestampMs: number | null; index: number },
  windowMs: number,
): string | null => {
  if (candidates.length === 0) return null;
  if (!Number.isFinite(source.index)) {
    return candidates[0]?.id ?? null;
  }
  const sourceTime = source.timestampMs;

  // Prefer timestamp matching when possible.
  if (sourceTime !== null) {
    let bestId: string | null = null;
    let bestDiff = Number.POSITIVE_INFINITY;
    for (const candidate of candidates) {
      if (candidate.timestampMs === null) continue;
      const diff = Math.abs(candidate.timestampMs - sourceTime);
      if (diff > windowMs) continue;
      if (diff < bestDiff) {
        bestDiff = diff;
        bestId = candidate.id;
      }
    }
    if (bestId) return bestId;
  }

  // Fallback: pick the closest candidate by relative array index.
  let bestId: string | null = null;
  let bestDiff = Number.POSITIVE_INFINITY;
  for (const candidate of candidates) {
    const diff = Math.abs(candidate.index - source.index);
    if (diff < bestDiff) {
      bestDiff = diff;
      bestId = candidate.id;
    }
  }
  return bestId;
};

/**
 * Remap streaming tool anchors onto the current message list.
 *
 * During streaming we anchor tool events to ephemeral message ids like `user-<Date.now()>`.
 * Once persisted messages load, `dedupeAndSortMessages()` can drop those placeholders in favor
 * of server-backed messages (timestamp ids). Without remapping, tool cards become "unanchored"
 * and fall to the bottom of the thread.
 */
export function reanchorToolEventAnchors(
  anchors: ToolEventAnchors,
  sourceMessages: ChatMessage[],
  targetMessages: ChatMessage[],
  options?: { windowMs?: number },
): ToolEventAnchors {
  const entries = Object.entries(anchors);
  if (entries.length === 0) return anchors;

  const targetIdSet = new Set(targetMessages.map((message) => message.id));
  const candidatesBySignature = buildCandidatesBySignature(targetMessages);
  const sourceCandidatesBySignature = buildCandidatesBySignature(sourceMessages);
  const sourceById = new Map(sourceMessages.map((message) => [message.id, message]));
  const sourceIndexById = new Map(sourceMessages.map((message, index) => [message.id, index]));
  const windowMs = options?.windowMs ?? ANCHOR_MATCH_WINDOW_MS;

  const resolved: ToolEventAnchors = {};

  for (const [anchorId, toolIds] of entries) {
    if (toolIds.length === 0) continue;

    let resolvedAnchorId: string | null = null;

    if (targetIdSet.has(anchorId)) {
      resolvedAnchorId = anchorId;
    } else {
      const source = sourceById.get(anchorId);
      const sourceTimestampMs = parseTimestampMs(source?.timestamp ?? null);
      if (source) {
        const signature = messageSignature(source);
        const candidates = candidatesBySignature.get(signature) ?? [];
        // First try an ordinal match among messages with the same signature.
        const sourceCandidates = sourceCandidatesBySignature.get(signature) ?? [];
        const ordinal = findOrdinal(sourceCandidates, anchorId);
        if (ordinal !== null && ordinal < candidates.length) {
          resolvedAnchorId = candidates[ordinal]?.id ?? null;
        } else {
          const sourceIndex = sourceIndexById.get(anchorId) ?? Number.POSITIVE_INFINITY;
          resolvedAnchorId = findClosestCandidateId(
            candidates,
            {
              timestampMs: sourceTimestampMs,
              index: sourceIndex,
            },
            windowMs,
          );
        }
      }
    }

    if (!resolvedAnchorId || !targetIdSet.has(resolvedAnchorId)) continue;

    const existing = resolved[resolvedAnchorId] ?? [];
    const deduped = new Set(existing);
    const nextIds = [...existing];
    for (const toolId of toolIds) {
      if (!toolId || deduped.has(toolId)) continue;
      deduped.add(toolId);
      nextIds.push(toolId);
    }
    resolved[resolvedAnchorId] = nextIds;
  }

  return resolved;
}
