import { describe, expect, it } from 'vitest';

import { parseSseStream } from '../sseParser';

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder();
  return new ReadableStream<Uint8Array>({
    start(controller) {
      for (const chunk of chunks) {
        controller.enqueue(encoder.encode(chunk));
      }
      controller.close();
    },
  });
}

describe('parseSseStream', () => {
  it('ignores comment heartbeats and yields data events', async () => {
    const stream = streamFromChunks([
      ': heartbeat 1\n\n',
      'data: {"ok":true}\n\n',
    ]);

    const events: string[] = [];
    for await (const evt of parseSseStream(stream)) {
      events.push(evt.data);
    }

    expect(events).toEqual(['{"ok":true}']);
  });

  it('joins multi-line data blocks with newlines', async () => {
    const stream = streamFromChunks([
      'data: line-1\n',
      'data: line-2\n\n',
    ]);

    const events: string[] = [];
    for await (const evt of parseSseStream(stream)) {
      events.push(evt.data);
    }

    expect(events).toEqual(['line-1\nline-2']);
  });

  it('supports CRLF framing', async () => {
    const stream = streamFromChunks(['data: {"a":1}\r\n\r\n']);

    const events: string[] = [];
    for await (const evt of parseSseStream(stream)) {
      events.push(evt.data);
    }

    expect(events).toEqual(['{"a":1}']);
  });

  it('handles event boundaries across chunks', async () => {
    const stream = streamFromChunks([
      'data: {"a":',
      '1}\n',
      '\n',
      'data: {"b":2}\n\n',
    ]);

    const events: string[] = [];
    for await (const evt of parseSseStream(stream)) {
      events.push(evt.data);
    }

    expect(events).toEqual(['{"a":1}', '{"b":2}']);
  });
});

