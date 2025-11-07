'use client';

import { useEffect, useRef, useState } from 'react';

import { readClientSessionMeta } from '@/lib/auth/clientMeta';

export type BillingEvent = {
  tenant_id: string;
  event_type: string;
  stripe_event_id: string;
  occurred_at: string;
  summary?: string | null;
  status: string;
};

export type BillingStreamStatus = 'disabled' | 'connecting' | 'open' | 'error';

export function useBillingStream() {
  const [events, setEvents] = useState<BillingEvent[]>([]);
  const [status, setStatus] = useState<BillingStreamStatus>('connecting');
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    const meta = readClientSessionMeta();
    if (!meta?.tenantId) {
      setStatus('disabled');
      return undefined;
    }

    let cancelled = false;
    const controller = new AbortController();
    abortRef.current = controller;

    async function connect() {
      try {
        const response = await fetch('/api/v1/billing/stream', {
          headers: {
            'X-Tenant-Id': meta.tenantId,
            'X-Tenant-Role': 'owner',
          },
          cache: 'no-store',
          signal: controller.signal,
        });
        if (!response.ok || !response.body) {
          throw new Error(`Stream failed (${response.status})`);
        }
        setStatus('open');
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        while (!cancelled) {
          const { value, done } = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, { stream: true });
          let boundary = buffer.indexOf('\n\n');
          while (boundary !== -1) {
            const chunk = buffer.slice(0, boundary);
            buffer = buffer.slice(boundary + 2);
            processChunk(chunk);
            boundary = buffer.indexOf('\n\n');
          }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          console.warn('[billing] stream connection failed', error);
          setStatus('error');
        }
      }
    }

    function processChunk(chunk: string) {
      const trimmed = chunk.trim();
      if (!trimmed || trimmed.startsWith(':')) {
        return;
      }
      if (trimmed.startsWith('data:')) {
        const data = trimmed.replace(/^data:\s*/, '');
        try {
          const payload = JSON.parse(data) as BillingEvent;
          setEvents((previous) => [payload, ...previous].slice(0, 20));
        } catch (error) {
          console.warn('[billing] failed to parse stream payload', error);
        }
      }
    }

    connect();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, []);

  return { events, status } as const;
}
