import { useEffect, useRef, useState } from 'react';

import { openActivityStream } from '@/lib/streams/activity';
import type { ActivityEvent } from '@/types/activity';

interface UseActivityStreamOptions {
  enabled?: boolean;
}

type StreamStatus = 'idle' | 'connecting' | 'open' | 'closed' | 'error';

export function useActivityStream(options?: UseActivityStreamOptions) {
  const [events, setEvents] = useState<ActivityEvent[]>([]);
  const [status, setStatus] = useState<StreamStatus>('idle');
  const sourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    if (options?.enabled === false) {
      return;
    }

    const source = openActivityStream({
      onOpen: () => setStatus('open'),
      onError: () => setStatus('error'),
      onEvent: (event) => {
        const data = event.data as unknown;
        if (data && typeof data === 'object' && 'action' in (data as Record<string, unknown>)) {
          setEvents((prev) => [data as ActivityEvent, ...prev].slice(0, 50));
        }
      },
    });
    sourceRef.current = source;

    return () => {
      sourceRef.current?.close();
      setStatus('closed');
    };
  }, [options?.enabled]);

  return { events, status };
}
