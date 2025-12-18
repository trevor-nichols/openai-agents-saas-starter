import { describe, expect, it, vi } from 'vitest';

import type { StreamingWorkflowEvent, WorkflowDescriptorResponse } from '@/lib/api/client/types.gen';
import { createWorkflowNodeStreamStore, type WorkflowNodeStreamStoreHandle } from '../nodeStreamStore';

const descriptor: WorkflowDescriptorResponse = {
  key: 'wf_1',
  display_name: 'Workflow',
  description: 'desc',
  default: false,
  allow_handoff_agents: false,
  step_count: 1,
  stages: [
    {
      name: 'stage0',
      mode: 'sequential',
      reducer: null,
      steps: [
        { name: 'Step A', agent_key: 'agent_a', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
  ],
  output_schema: null,
};

const base = {
  schema: 'public_sse_v1',
  stream_id: 'stream_1',
  server_timestamp: '2025-12-16T00:00:00.000Z',
  conversation_id: 'conv_1',
  provider_sequence_number: 1,
  notices: null,
  workflow: {
    workflow_key: 'wf_1',
    workflow_run_id: 'run_1',
    stage_name: 'stage0',
    step_name: 'Step A',
    step_agent: 'agent_a',
    parallel_group: null,
    branch_index: null,
  },
} as const;

function e<T extends StreamingWorkflowEvent>(event: T): StreamingWorkflowEvent {
  return event as StreamingWorkflowEvent;
}

describe('Workflow node stream store', () => {
  it('accumulates message deltas and exposes snapshots per node', () => {
    const scheduler = {
      schedule: (cb: () => void) => {
        cb();
        return 0;
      },
      cancel: (_handle: WorkflowNodeStreamStoreHandle) => {},
    };

    const store = createWorkflowNodeStreamStore({ descriptor, scheduler });
    const notify = vi.fn();
    const unsubscribe = store.subscribe('0:0', notify);

    store.applyEvents([
      e({
        ...base,
        event_id: 1,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 0,
        item_id: 'msg_1',
        content_index: 0,
        delta: 'Hello',
      }),
      e({
        ...base,
        event_id: 2,
        kind: 'output_item.done',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 0,
        item_id: 'msg_1',
        item_type: 'message',
        role: 'assistant',
        status: 'completed',
      }),
    ]);

    expect(notify).toHaveBeenCalled();
    const snap = store.getSnapshot('0:0');
    expect(snap.items).toHaveLength(1);
    expect(snap.items[0]).toMatchObject({ kind: 'message', itemId: 'msg_1', outputIndex: 0 });
    expect((snap.items[0] as any).text).toBe('Hello');

    unsubscribe();
    store.destroy();
  });

  it('shows tool placeholders and updates status from tool.status', () => {
    const scheduler = {
      schedule: (cb: () => void) => {
        cb();
        return 0;
      },
      cancel: (_handle: WorkflowNodeStreamStoreHandle) => {},
    };

    const store = createWorkflowNodeStreamStore({
      descriptor,
      scheduler,
      config: { maxPreviewItems: 3, maxRetainedItems: 10 },
    });

    store.applyEvents([
      e({
        ...base,
        event_id: 1,
        kind: 'output_item.added',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 0,
        item_id: 'tool_1',
        item_type: 'web_search_call',
        role: null,
        status: null,
      }),
    ]);

    let snap = store.getSnapshot('0:0');
    expect(snap.items[0]).toMatchObject({ kind: 'tool', itemId: 'tool_1', label: 'web_search', status: 'running' });

    store.applyEvents([
      e({
        ...base,
        event_id: 2,
        kind: 'tool.status',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 0,
        item_id: 'tool_1',
        tool: {
          tool_type: 'web_search',
          tool_call_id: 'tool_1',
          status: 'completed',
          query: 'openai agents sdk',
          sources: [],
        },
      }),
    ]);

    snap = store.getSnapshot('0:0');
    expect(snap.items[0]).toMatchObject({ kind: 'tool', itemId: 'tool_1', status: 'done' });
    expect((snap.items[0] as any).inputPreview).toBe('openai agents sdk');
    store.destroy();
  });

  it('truncates to the last N preview items and reports overflow', () => {
    const scheduler = {
      schedule: (cb: () => void) => {
        cb();
        return 0;
      },
      cancel: (_handle: WorkflowNodeStreamStoreHandle) => {},
    };

    const store = createWorkflowNodeStreamStore({
      descriptor,
      scheduler,
      config: { maxPreviewItems: 2, maxRetainedItems: 5 },
    });

    store.applyEvents([
      e({
        ...base,
        event_id: 1,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 0,
        item_id: 'msg_0',
        content_index: 0,
        delta: '0',
      }),
      e({
        ...base,
        event_id: 2,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 1,
        item_id: 'msg_1',
        content_index: 0,
        delta: '1',
      }),
      e({
        ...base,
        event_id: 3,
        kind: 'message.delta',
        response_id: 'resp_1',
        agent: 'agent_a',
        output_index: 2,
        item_id: 'msg_2',
        content_index: 0,
        delta: '2',
      }),
    ]);

    const snap = store.getSnapshot('0:0');
    expect(snap.items).toHaveLength(2);
    expect(snap.items.map((i) => i.itemId)).toEqual(['msg_1', 'msg_2']);
    expect(snap.overflowCount).toBe(1);
    store.destroy();
  });
});
