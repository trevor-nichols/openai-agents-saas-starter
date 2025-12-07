import { useEffect, useRef } from 'react';

import { openConversationMetadataStream } from '@/lib/streams/conversationMetadata';

type ConversationMetadataEvent = {
  data?: unknown;
};

interface UseConversationMetadataOptions {
  conversationId: string | null;
  onTitle: (title: string) => void;
  onPendingStart?: () => void;
  onPendingResolve?: () => void;
  timeoutMs?: number;
}

/**
 * Subscribe to conversation metadata SSE (e.g., generated titles) and invoke a callback on updates.
 */
export function useConversationMetadata({
  conversationId,
  onTitle,
  onPendingStart,
  onPendingResolve,
  timeoutMs = 1800,
}: UseConversationMetadataOptions) {
  const lastTitleRef = useRef<string | null>(null);
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
    timeoutRef.current = setTimeout(() => {
      onPendingResolveRef.current?.();
      timeoutRef.current = null;
    }, timeoutMs);

    const source = openConversationMetadataStream({
      conversationId,
      onEvent: (event: ConversationMetadataEvent) => {
        const payload = event?.data as { display_name?: string | null } | null;
        const title = payload?.display_name ?? null;
        if (!title || title === lastTitleRef.current) {
          return;
        }
        lastTitleRef.current = title;
        onPendingResolveRef.current?.();
        onTitleRef.current(title);
      },
      onError: () => {
        // Fail open: metadata stream is best-effort; do nothing on errors.
      },
    });

    return () => {
      lastTitleRef.current = null;
      onPendingResolveRef.current?.();
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      source.close();
    };
  }, [conversationId, timeoutMs]);
}
