import { describe, expect, it } from 'vitest';

import type { StreamingWorkflowEvent, WorkflowDescriptorResponse } from '@/lib/api/client/types.gen';
import { buildWorkflowDescriptorIndex, resolveWorkflowNodeIdForEvent } from '../descriptorIndex';

const descriptor: WorkflowDescriptorResponse = {
  key: 'wf_1',
  display_name: 'Workflow',
  description: 'desc',
  default: false,
  allow_handoff_agents: false,
  step_count: 4,
  stages: [
    {
      name: 'stage0',
      mode: 'sequential',
      reducer: null,
      steps: [
        { name: 'Step A', agent_key: 'agent_a', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Step B', agent_key: 'agent_b', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
      ],
    },
    {
      name: 'stage1',
      mode: 'parallel',
      reducer: null,
      steps: [
        { name: 'Notify A', agent_key: 'agent_c', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
        { name: 'Notify B', agent_key: 'agent_d', guard: null, guard_type: null, input_mapper: null, input_mapper_type: null, max_turns: null, output_schema: null },
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
} as const;

function e<T extends StreamingWorkflowEvent>(event: T): StreamingWorkflowEvent {
  return event as StreamingWorkflowEvent;
}

describe('Workflow descriptor index', () => {
  it('resolves exact stage+step+branch to the graph node id', () => {
    const index = buildWorkflowDescriptorIndex(descriptor);
    const event = e({
      ...base,
      event_id: 1,
      kind: 'message.delta',
      response_id: 'resp_1',
      agent: 'agent_b',
      workflow: {
        workflow_key: 'wf_1',
        workflow_run_id: 'run_1',
        stage_name: 'stage0',
        step_name: 'Step B',
        step_agent: 'agent_b',
        parallel_group: null,
        branch_index: null,
      },
      output_index: 0,
      item_id: 'msg_1',
      content_index: 0,
      delta: 'Hello',
    });

    expect(resolveWorkflowNodeIdForEvent(index, event)).toBe('0:1');
  });

  it('falls back to stage+agent+branch when step_name is missing', () => {
    const index = buildWorkflowDescriptorIndex(descriptor);
    const event = e({
      ...base,
      event_id: 2,
      kind: 'message.delta',
      response_id: 'resp_2',
      agent: 'agent_a',
      workflow: {
        workflow_key: 'wf_1',
        workflow_run_id: 'run_1',
        stage_name: 'stage0',
        step_name: null,
        step_agent: 'agent_a',
        parallel_group: null,
        branch_index: null,
      },
      output_index: 0,
      item_id: 'msg_2',
      content_index: 0,
      delta: 'Hi',
    });

    expect(resolveWorkflowNodeIdForEvent(index, event)).toBe('0:0');
  });

  it('does not require step_agent when step_name is present (primary identity)', () => {
    const index = buildWorkflowDescriptorIndex(descriptor);
    const event = e({
      ...base,
      event_id: 20,
      kind: 'message.delta',
      response_id: 'resp_20',
      agent: 'agent_b',
      workflow: {
        workflow_key: 'wf_1',
        workflow_run_id: 'run_1',
        stage_name: 'stage0',
        step_name: 'Step B',
        step_agent: null,
        parallel_group: null,
        branch_index: null,
      },
      output_index: 0,
      item_id: 'msg_20',
      content_index: 0,
      delta: 'Hello',
    });

    expect(resolveWorkflowNodeIdForEvent(index, event)).toBe('0:1');
  });

  it('uses branch_index to disambiguate parallel steps', () => {
    const index = buildWorkflowDescriptorIndex(descriptor);
    const event = e({
      ...base,
      event_id: 3,
      kind: 'message.delta',
      response_id: 'resp_3',
      agent: 'agent_d',
      workflow: {
        workflow_key: 'wf_1',
        workflow_run_id: 'run_1',
        stage_name: 'stage1',
        step_name: 'Notify B',
        step_agent: 'agent_d',
        parallel_group: 'stage1',
        branch_index: 1,
      },
      output_index: 0,
      item_id: 'msg_3',
      content_index: 0,
      delta: 'Done',
    });

    expect(resolveWorkflowNodeIdForEvent(index, event)).toBe('1:1');
  });

  it('ignores events for other workflows when workflow_key is present', () => {
    const index = buildWorkflowDescriptorIndex(descriptor);
    const event = e({
      ...base,
      event_id: 4,
      kind: 'message.delta',
      response_id: 'resp_4',
      agent: 'agent_b',
      workflow: {
        workflow_key: 'wf_other',
        workflow_run_id: 'run_2',
        stage_name: 'stage0',
        step_name: 'Step B',
        step_agent: 'agent_b',
        parallel_group: null,
        branch_index: null,
      },
      output_index: 0,
      item_id: 'msg_4',
      content_index: 0,
      delta: 'Hello',
    });

    expect(resolveWorkflowNodeIdForEvent(index, event)).toBeNull();
  });
});
