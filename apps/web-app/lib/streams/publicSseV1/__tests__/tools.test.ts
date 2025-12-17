import { describe, expect, it } from 'vitest';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';
import { createPublicSseToolAccumulator } from '@/lib/streams/publicSseV1/tools';

const base = (kind: PublicSseEvent['kind']) =>
  ({
    schema: 'public_sse_v1',
    event_id: 1,
    stream_id: 'stream-test',
    server_timestamp: '2025-12-17T00:00:00.000Z',
    kind,
    output_index: 0,
    item_id: 'item_1',
  }) as unknown as PublicSseEvent;

describe('publicSseV1 tools accumulator', () => {
  it('links placeholders by item_id to tool_call_id updates via aliasing', () => {
    const acc = createPublicSseToolAccumulator();

    acc.apply({
      ...base('output_item.added'),
      output_index: 0,
      item_id: 'item_123',
      item_type: 'mcp_call',
      role: 'assistant',
      status: 'in_progress',
    } as unknown as PublicSseEvent);

    acc.apply({
      ...base('tool.arguments.delta'),
      output_index: 0,
      item_id: 'item_123',
      tool_call_id: 'call_abc',
      tool_type: 'mcp',
      tool_name: 'stripe.create_payment_link',
      delta: '{ "amount": 10',
    } as unknown as PublicSseEvent);

    acc.apply({
      ...base('tool.status'),
      output_index: 0,
      item_id: 'item_123',
      tool: {
        tool_type: 'mcp',
        tool_call_id: 'call_abc',
        status: 'awaiting_approval',
        server_label: 'stripe',
        tool_name: 'stripe.create_payment_link',
        arguments_text: '{ "amount": 10',
        arguments_json: null,
        output: null,
      },
    } as unknown as PublicSseEvent);

    const tools = acc.getToolsSorted();
    expect(tools).toHaveLength(1);
    expect(tools[0]?.id).toBe('call_abc');
    expect(tools[0]?.name).toBe('stripe.create_payment_link');
    expect((tools[0]?.input as any)?.tool_type).toBe('mcp');
  });

  it('projects tool.approval as a visible tool output', () => {
    const acc = createPublicSseToolAccumulator();

    acc.apply({
      ...base('tool.approval'),
      output_index: 0,
      item_id: 'mcp_item',
      tool_call_id: 'mcp_item',
      tool_type: 'mcp',
      tool_name: 'stripe.create_payment_link',
      server_label: 'stripe',
      approval_request_id: 'mcpr_1',
      approved: true,
      reason: 'ok',
    } as unknown as PublicSseEvent);

    const tools = acc.getToolsSorted();
    expect(tools).toHaveLength(1);
    expect(tools[0]?.status).toBe('output-available');
    expect((tools[0]?.output as any)?.approved).toBe(true);
    expect((tools[0]?.output as any)?.approval_request_id).toBe('mcpr_1');
  });
});

