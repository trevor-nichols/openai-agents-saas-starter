/**
 * SSE client for activity events.
 *
 * Reuses the generated SDK path and bearer auth from cookies via a server helper.
 * This is browser-only (no Next.js caching). Callers should close the stream on unmount.
 */

export type ActivityStreamHandler = (event: { data: unknown }) => void;

export interface ActivityStreamOptions {
  onEvent: ActivityStreamHandler;
  onError?: (error: Event) => void;
  onOpen?: () => void;
}

export function openActivityStream(options: ActivityStreamOptions): EventSource {
  const url = `/api/v1/activity/stream`;

  // Auth is handled server-side via the proxy route and cookies.
  const source = new EventSource(url);

  source.onmessage = (event) => {
    if (!event.data) return;
    try {
      const parsed = JSON.parse(event.data);
      options.onEvent({ data: parsed });
    } catch {
      options.onEvent({ data: event.data });
    }
  };

  if (options.onError) {
    source.onerror = options.onError;
  }
  if (options.onOpen) {
    source.onopen = options.onOpen;
  }

  return source;
}
