/**
 * API Layer - Billing SSE stream connection
 *
 * Handles Server-Sent Events (SSE) connection for real-time billing events
 */

import type { BillingEvent } from '@/types/billing';

/**
 * Connect to the billing events SSE stream
 *
 * @param onEvent - Callback when a new event is received
 * @param onStatusChange - Callback when connection status changes
 * @param signal - AbortSignal for cleanup
 */
export async function connectBillingStream(
  onEvent: (event: BillingEvent) => void,
  onStatusChange: (status: 'connecting' | 'open' | 'error') => void,
  signal: AbortSignal
): Promise<void> {
  try {
    const response = await fetch('/api/billing/stream', {
      cache: 'no-store',
      signal,
      credentials: 'include',
    });

    if (!response.ok || !response.body) {
      throw new Error(`Stream failed (${response.status})`);
    }

    onStatusChange('open');

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (!signal.aborted) {
      const { value, done } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      let boundary = buffer.indexOf('\n\n');

      while (boundary !== -1) {
        const chunk = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        processChunk(chunk, onEvent);
        boundary = buffer.indexOf('\n\n');
      }
    }
  } catch (error) {
    if (!signal.aborted) {
      console.warn('[billing] stream connection failed', error);
      onStatusChange('error');
    }
  }
}

/**
 * Process a single SSE chunk
 */
function processChunk(chunk: string, onEvent: (event: BillingEvent) => void): void {
  const trimmed = chunk.trim();

  // Ignore empty lines and comments
  if (!trimmed || trimmed.startsWith(':')) {
    return;
  }

  // Parse data lines
  if (trimmed.startsWith('data:')) {
    const data = trimmed.replace(/^data:\s*/, '');
    try {
      const payload = JSON.parse(data) as BillingEvent;
      onEvent(payload);
    } catch (error) {
      console.warn('[billing] failed to parse stream payload', error);
    }
  }
}
