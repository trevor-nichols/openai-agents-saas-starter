/**
 * Robust Server-Sent Events (SSE) parser for fetch-based streams (POST + body).
 *
 * Supports:
 * - Comment heartbeats (`: heartbeat ...`)
 * - Multi-line `data:` blocks (joined with `\n` per SSE spec)
 * - `\n` and `\r\n` line endings
 *
 * Notes:
 * - This parser is intentionally small and dependency-free so it can be shared
 *   across chat + workflow streaming consumers.
 * - We only yield events that contain at least one `data:` line.
 */

export type SseEvent = {
  data: string;
  event?: string;
  id?: string;
  retry?: number;
};

export interface ParseSseStreamOptions {
  signal?: AbortSignal;
}

function parseLine(line: string): { field: string; value: string } {
  const colonIndex = line.indexOf(':');
  if (colonIndex === -1) {
    return { field: line, value: '' };
  }
  const field = line.slice(0, colonIndex);
  let value = line.slice(colonIndex + 1);
  if (value.startsWith(' ')) value = value.slice(1);
  return { field, value };
}

/**
 * Parse an SSE byte stream into discrete events.
 */
export async function* parseSseStream(
  stream: ReadableStream<Uint8Array>,
  options: ParseSseStreamOptions = {},
): AsyncGenerator<SseEvent, void, unknown> {
  const reader = stream.getReader();
  const decoder = new TextDecoder();
  let readerClosed = false;

  // Per SSE spec, `id` persists across events (used for reconnection).
  let lastEventId: string | undefined;
  let retry: number | undefined;

  // Reset per dispatched event.
  let eventName: string | undefined;
  let dataLines: string[] = [];

  let buffer = '';

  const flushEvent = (): SseEvent | null => {
    if (dataLines.length === 0) {
      eventName = undefined;
      return null;
    }
    const data = dataLines.join('\n');
    dataLines = [];
    const evt: SseEvent = { data, event: eventName, id: lastEventId, retry };
    eventName = undefined;
    return evt;
  };

  const abortHandler = () => {
    try {
      reader.cancel();
    } catch {
      // noop
    }
  };

  options.signal?.addEventListener('abort', abortHandler);

  try {
    while (true) {
      if (options.signal?.aborted) break;

      const { done, value } = await reader.read();
      if (done) {
        readerClosed = true;
        break;
      }

      buffer += decoder.decode(value, { stream: true });

      let newlineIndex = buffer.indexOf('\n');
      while (newlineIndex !== -1) {
        let line = buffer.slice(0, newlineIndex);
        buffer = buffer.slice(newlineIndex + 1);
        newlineIndex = buffer.indexOf('\n');

        // Handle CRLF.
        if (line.endsWith('\r')) line = line.slice(0, -1);

        // Blank line => dispatch event.
        if (line === '') {
          const evt = flushEvent();
          if (evt) yield evt;
          continue;
        }

        // Comment line (heartbeat) => ignore.
        if (line.startsWith(':')) {
          continue;
        }

        const { field, value: fieldValue } = parseLine(line);

        if (field === 'data') {
          dataLines.push(fieldValue);
          continue;
        }

        if (field === 'event') {
          eventName = fieldValue;
          continue;
        }

        if (field === 'id') {
          lastEventId = fieldValue;
          continue;
        }

        if (field === 'retry') {
          const parsed = Number.parseInt(fieldValue, 10);
          if (!Number.isNaN(parsed)) retry = parsed;
        }
      }
    }

    // Flush any trailing (non-newline terminated) content as a final line.
    if (buffer.length > 0) {
      let line = buffer;
      if (line.endsWith('\r')) line = line.slice(0, -1);
      buffer = '';

      if (line === '') {
        const evt = flushEvent();
        if (evt) yield evt;
      } else if (!line.startsWith(':')) {
        const { field, value: fieldValue } = parseLine(line);
        if (field === 'data') dataLines.push(fieldValue);
        if (field === 'event') eventName = fieldValue;
        if (field === 'id') lastEventId = fieldValue;
        if (field === 'retry') {
          const parsed = Number.parseInt(fieldValue, 10);
          if (!Number.isNaN(parsed)) retry = parsed;
        }
      }
    }

    const evt = flushEvent();
    if (evt) yield evt;
  } finally {
    options.signal?.removeEventListener('abort', abortHandler);
    if (!readerClosed) {
      try {
        await reader.cancel();
      } catch {
        // noop
      }
    }
    reader.releaseLock();
  }
}
