import { useCallback, useEffect, useRef, type Dispatch } from 'react';

import type { MessagesAction } from '../state/messagesReducer';

export function useMessageDispatchQueue(dispatch: Dispatch<MessagesAction>) {
  const queueRef = useRef<MessagesAction[]>([]);
  const frameRef = useRef<number | null>(null);

  const flushQueuedMessages = useCallback(() => {
    if (!queueRef.current.length) {
      frameRef.current = null;
      return;
    }
    dispatch({ type: 'batch', actions: queueRef.current });
    queueRef.current = [];
    frameRef.current = null;
  }, [dispatch]);

  const enqueueMessageAction = useCallback(
    (action: MessagesAction) => {
      queueRef.current.push(action);
      if (frameRef.current === null) {
        frameRef.current = requestAnimationFrame(flushQueuedMessages);
      }
    },
    [flushQueuedMessages],
  );

  useEffect(() => {
    return () => {
      if (frameRef.current !== null) {
        cancelAnimationFrame(frameRef.current);
      }
      queueRef.current = [];
    };
  }, []);

  return { enqueueMessageAction, flushQueuedMessages };
}

