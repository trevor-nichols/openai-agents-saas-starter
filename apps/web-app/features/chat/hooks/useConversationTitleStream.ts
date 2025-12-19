import { useEffect, useRef } from 'react';

import { openConversationTitleStream } from '@/lib/streams/conversationTitle';

interface UseConversationMetadataOptions {
  conversationId: string | null;
  onTitle: (title: string) => void;
  onPendingStart?: () => void;
  onPendingResolve?: () => void;
  timeoutMs?: number;
}

/**
 * Subscribe to the conversation title SSE stream and invoke callbacks as the title is generated.
 */
export function useConversationTitleStream({
  conversationId,
  onTitle,
  onPendingStart,
  onPendingResolve,
  timeoutMs = 5000,
}: UseConversationMetadataOptions) {
  const lastTitleRef = useRef<string | null>(null);
  const bufferRef = useRef<string>('');
  const resolvedRef = useRef(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const onTitleRef = useRef(onTitle);
  const onPendingStartRef = useRef(onPendingStart);
  const onPendingResolveRef = useRef(onPendingResolve);

  useEffect(() => {
    onTitleRef.current = onTitle;
  }, [onTitle]);

  useEffect(() => {
    onPendingStartRef.current = onPendingStart;
  }, [onPendingStart]);

  useEffect(() => {
    onPendingResolveRef.current = onPendingResolve;
  }, [onPendingResolve]);

  useEffect(() => {
    if (!conversationId) {
      return;
    }

    onPendingStartRef.current?.();
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    bufferRef.current = '';
    lastTitleRef.current = null;
    resolvedRef.current = false;

    const resolvePending = () => {
      if (resolvedRef.current) return;
      resolvedRef.current = true;
      onPendingResolveRef.current?.();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
    };

    timeoutRef.current = setTimeout(resolvePending, timeoutMs);

    const source = openConversationTitleStream({
      conversationId,
      onMessage: (message: string) => {
        if (!message) return;
        if (message === '[DONE]') {
          resolvePending();
          source.close(); // prevent automatic EventSource reconnects
          return;
        }

        bufferRef.current += message;
        const title = bufferRef.current.trim();
        if (!title || title === lastTitleRef.current) return;
        lastTitleRef.current = title;
        onTitleRef.current(title);
      },
      onError: () => {
        // Fail open: title stream is best-effort; keep the UI responsive.
        resolvePending();
        source.close();
      },
    });

    return () => {
      bufferRef.current = '';
      lastTitleRef.current = null;
      resolvePending();
      source.close();
    };
  }, [conversationId, timeoutMs]);
}
