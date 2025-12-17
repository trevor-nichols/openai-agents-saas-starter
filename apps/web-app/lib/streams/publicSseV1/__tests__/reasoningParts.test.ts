import { describe, expect, it } from 'vitest';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import { applyReasoningEvent, createReasoningPartsState, getReasoningParts } from '@/lib/streams/publicSseV1/reasoningParts';

const base = (kind: PublicSseEvent['kind']) =>
  ({
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id: 'stream-test',
    server_timestamp: '2025-12-17T00:00:00.000Z',
    kind,
  }) as unknown as PublicSseEvent;

describe('publicSseV1 reasoning parts', () => {
  it('accumulates deltas into the correct summary_index part', () => {
    const state = createReasoningPartsState();

    applyReasoningEvent(state, {
      ...base('reasoning_summary.part.added'),
      output_index: 0,
      item_id: 'rs_1',
      summary_index: 0,
      part_type: 'summary_text',
      text: '',
    } as unknown as PublicSseEvent);

    applyReasoningEvent(state, {
      ...base('reasoning_summary.delta'),
      output_index: 0,
      item_id: 'rs_1',
      summary_index: 0,
      delta: 'First. ',
    } as unknown as PublicSseEvent);

    applyReasoningEvent(state, {
      ...base('reasoning_summary.delta'),
      output_index: 0,
      item_id: 'rs_1',
      summary_index: 0,
      delta: 'Second.',
    } as unknown as PublicSseEvent);

    const parts = getReasoningParts(state);
    expect(parts).toEqual([{ summaryIndex: 0, status: 'streaming', text: 'First. Second.' }]);
  });

  it('overwrites with authoritative text on part.done and marks done', () => {
    const state = createReasoningPartsState();

    applyReasoningEvent(state, {
      ...base('reasoning_summary.part.added'),
      output_index: 0,
      item_id: 'rs_2',
      summary_index: 1,
      part_type: 'summary_text',
      text: '',
    } as unknown as PublicSseEvent);

    applyReasoningEvent(state, {
      ...base('reasoning_summary.delta'),
      output_index: 0,
      item_id: 'rs_2',
      summary_index: 1,
      delta: 'Draft...',
    } as unknown as PublicSseEvent);

    applyReasoningEvent(state, {
      ...base('reasoning_summary.part.done'),
      output_index: 0,
      item_id: 'rs_2',
      summary_index: 1,
      part_type: 'summary_text',
      text: 'Final part',
    } as unknown as PublicSseEvent);

    const parts = getReasoningParts(state);
    expect(parts).toEqual([{ summaryIndex: 1, status: 'done', text: 'Final part' }]);
  });
});

