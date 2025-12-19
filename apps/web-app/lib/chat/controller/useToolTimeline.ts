import { useMemo } from 'react';

import type { PublicSseEvent } from '@/lib/api/client/types.gen';

import type { ChatMessage, ToolEventAnchors, ToolState } from '../types';
import { mapLedgerEventsToToolTimeline } from '../mappers/ledgerReplayMappers';
import {
  mergeToolEventAnchors,
  mergeToolStates,
  reanchorToolEventAnchors,
} from '../mappers/toolTimelineMappers';

export interface UseToolTimelineParams {
  ledgerEvents: PublicSseEvent[] | undefined;
  historyMessagesWithMarkers: ChatMessage[];
  liveToolEvents: ToolState[];
  liveToolEventAnchors: ToolEventAnchors;
  liveMessages: ChatMessage[];
  mergedMessages: ChatMessage[];
}

export interface UseToolTimelineResult {
  toolEvents: ToolState[];
  toolEventAnchors: ToolEventAnchors;
}

export function useToolTimeline(params: UseToolTimelineParams): UseToolTimelineResult {
  const {
    ledgerEvents,
    historyMessagesWithMarkers,
    liveToolEvents,
    liveToolEventAnchors,
    liveMessages,
    mergedMessages,
  } = params;

  const persistedToolTimeline = useMemo(() => {
    if (!ledgerEvents?.length) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    if (historyMessagesWithMarkers.length === 0) {
      return { tools: [] as ToolState[], anchors: {} as ToolEventAnchors };
    }
    return mapLedgerEventsToToolTimeline(ledgerEvents, historyMessagesWithMarkers);
  }, [ledgerEvents, historyMessagesWithMarkers]);

  const toolEvents = useMemo(
    () => mergeToolStates(persistedToolTimeline.tools, liveToolEvents),
    [persistedToolTimeline.tools, liveToolEvents],
  );

  const reanchoredToolEventAnchors = useMemo(
    () => reanchorToolEventAnchors(liveToolEventAnchors, liveMessages, mergedMessages),
    [liveToolEventAnchors, liveMessages, mergedMessages],
  );

  const toolEventAnchors = useMemo(
    () => mergeToolEventAnchors(persistedToolTimeline.anchors, reanchoredToolEventAnchors),
    [persistedToolTimeline.anchors, reanchoredToolEventAnchors],
  );

  return { toolEvents, toolEventAnchors };
}

