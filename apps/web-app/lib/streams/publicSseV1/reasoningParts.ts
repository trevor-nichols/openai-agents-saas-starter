import type { PublicSseEvent } from '@/lib/api/client/types.gen';

export type ReasoningPart = {
  summaryIndex: number;
  status: 'streaming' | 'done';
  text: string;
};

export type ReasoningPartsState = {
  partsByIndex: Map<number, ReasoningPart>;
};

export function createReasoningPartsState(): ReasoningPartsState {
  return { partsByIndex: new Map() };
}

export function applyReasoningEvent(state: ReasoningPartsState, event: PublicSseEvent): void {
  if (event.kind === 'reasoning_summary.part.added') {
    if (typeof event.summary_index !== 'number') return;
    const existing = state.partsByIndex.get(event.summary_index);
    if (existing) return;
    state.partsByIndex.set(event.summary_index, {
      summaryIndex: event.summary_index,
      status: 'streaming',
      text: event.text ?? '',
    });
    return;
  }

  if (event.kind === 'reasoning_summary.delta') {
    if (typeof event.summary_index !== 'number') return;
    const summaryIndex = event.summary_index;
    const existing =
      state.partsByIndex.get(summaryIndex) ??
      ({
        summaryIndex,
        status: 'streaming',
        text: '',
      } satisfies ReasoningPart);
    state.partsByIndex.set(summaryIndex, {
      ...existing,
      text: `${existing.text}${event.delta}`,
    });
    return;
  }

  if (event.kind === 'reasoning_summary.part.done') {
    if (typeof event.summary_index !== 'number') return;
    state.partsByIndex.set(event.summary_index, {
      summaryIndex: event.summary_index,
      status: 'done',
      text: event.text,
    });
  }
}

export function getReasoningParts(state: ReasoningPartsState): ReasoningPart[] {
  return Array.from(state.partsByIndex.values()).sort((a, b) => a.summaryIndex - b.summaryIndex);
}

export function getReasoningSummaryText(state: ReasoningPartsState): string {
  return getReasoningParts(state)
    .map((part) => part.text)
    .join('');
}

export function appendReasoningSuffix(state: ReasoningPartsState, delta: string): void {
  if (!delta) return;
  const indices = Array.from(state.partsByIndex.keys());
  const summaryIndex = indices.length ? Math.max(...indices) : 0;
  const existing =
    state.partsByIndex.get(summaryIndex) ??
    ({
      summaryIndex,
      status: 'streaming',
      text: '',
    } satisfies ReasoningPart);
  state.partsByIndex.set(summaryIndex, { ...existing, text: `${existing.text}${delta}` });
}
