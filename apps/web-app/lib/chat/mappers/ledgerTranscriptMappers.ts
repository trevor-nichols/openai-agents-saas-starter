import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import type { CitationsState } from '@/lib/streams/publicSseV1/citations';
import { applyCitationEvent, createCitationsState, getCitationsForItem } from '@/lib/streams/publicSseV1/citations';
import { parseTimestampMs } from '@/lib/utils/time';

import type { Annotation, ChatMessage } from '../types';

type LedgerAssistantSummary = {
  timestampMs: number;
  responseText: string | null;
  structuredOutput: unknown | null;
  citations: Annotation[] | null;
};

type ResponseState = {
  lastMessageItemId: string | null;
  citations: CitationsState;
};

const SYSTEM_MESSAGE_PREFIX = '[system] ';
const LEDGER_SUMMARY_MATCH_WINDOW_MS = 5 * 60 * 1000;

function buildAssistantSummaries(events: PublicSseEvent[]): LedgerAssistantSummary[] {
  const byResponse = new Map<string, ResponseState>();
  const finals: Extract<PublicSseEvent, { kind: 'final' }>[] = [];

  for (const event of events) {
    const responseId = event.response_id;
    if (!responseId) continue;

    const state = byResponse.get(responseId) ?? {
      lastMessageItemId: null,
      citations: createCitationsState(),
    };

    if (event.kind === 'message.delta') {
      state.lastMessageItemId = event.item_id;
    }

    applyCitationEvent(state.citations, event);

    if (event.kind === 'final') {
      finals.push(event);
    }

    byResponse.set(responseId, state);
  }

  const summaries: LedgerAssistantSummary[] = [];
  for (const event of finals) {
    const timestampMs = parseTimestampMs(event.server_timestamp ?? null);
    if (timestampMs === null) continue;

    const responseId = event.response_id;
    const state = responseId ? byResponse.get(responseId) : undefined;
    const itemId = state?.lastMessageItemId;

    const responseText =
      event.final.response_text ??
      event.final.refusal_text ??
      null;

    summaries.push({
      timestampMs,
      responseText,
      structuredOutput: event.final.structured_output ?? null,
      citations: itemId && state ? getCitationsForItem(state.citations, itemId) : null,
    });
  }

  return summaries;
}

export function enrichChatMessagesFromLedger(events: PublicSseEvent[], messages: ChatMessage[]): ChatMessage[] {
  if (!events.length || !messages.length) return messages;

  const summaries = buildAssistantSummaries(events);
  if (summaries.length === 0) return messages;

  const out = messages.map((message) => ({ ...message }));

  const orderedSummaries = [...summaries].sort((a, b) => a.timestampMs - b.timestampMs);

  const enrichableAssistantMessages = out
    .map((message, index) => ({
      message,
      index,
      timestampMs: parseTimestampMs(message.timestamp ?? null),
    }))
    .filter(
      (entry) =>
        entry.message.role === 'assistant' &&
        entry.message.kind !== 'memory_checkpoint' &&
        !entry.message.content.startsWith(SYSTEM_MESSAGE_PREFIX) &&
        entry.timestampMs !== null,
    );

  let summaryIndex = 0;
  for (const entry of enrichableAssistantMessages) {
    const messageTimestampMs = entry.timestampMs;
    if (messageTimestampMs === null) continue;

    while (
      summaryIndex < orderedSummaries.length &&
      orderedSummaries[summaryIndex]!.timestampMs < messageTimestampMs - LEDGER_SUMMARY_MATCH_WINDOW_MS
    ) {
      summaryIndex += 1;
    }
    if (summaryIndex >= orderedSummaries.length) break;

    while (summaryIndex + 1 < orderedSummaries.length) {
      const current = orderedSummaries[summaryIndex]!;
      const next = orderedSummaries[summaryIndex + 1]!;
      const currentDiff = Math.abs(current.timestampMs - messageTimestampMs);
      const nextDiff = Math.abs(next.timestampMs - messageTimestampMs);
      if (nextDiff <= currentDiff) {
        summaryIndex += 1;
        continue;
      }
      break;
    }

    const candidate = orderedSummaries[summaryIndex];
    if (!candidate) break;
    const diff = Math.abs(candidate.timestampMs - messageTimestampMs);
    if (diff > LEDGER_SUMMARY_MATCH_WINDOW_MS) continue;

    const message = out[entry.index];
    if (!message) continue;

    if (candidate.responseText) {
      message.content = candidate.responseText;
    }
    if (candidate.structuredOutput !== null && candidate.structuredOutput !== undefined) {
      message.structuredOutput = candidate.structuredOutput;
    }
    if (candidate.citations?.length) {
      message.citations = candidate.citations;
    }

    summaryIndex += 1;
  }

  return out;
}
