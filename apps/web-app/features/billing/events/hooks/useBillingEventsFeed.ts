'use client';

import { useMemo } from 'react';

import { useBillingStream } from '@/lib/queries/billing';
import { useBillingHistory } from '@/lib/queries/billingHistory';
import type { BillingEventProcessingStatus, BillingEvent } from '@/types/billing';

import { mergeBillingEvents } from '../../shared/utils/mergeEvents';

interface UseBillingEventsFeedOptions {
  pageSize?: number;
  eventType?: string | null;
  processingStatus?: BillingEventProcessingStatus | 'all';
}

interface UseBillingEventsFeedResult {
  events: BillingEvent[];
  streamStatus: ReturnType<typeof useBillingStream>['status'];
  isLoading: boolean;
  isFetchingMore: boolean;
  hasNextPage: boolean;
  loadMore: () => Promise<void>;
  refetch: () => Promise<void>;
}

export function useBillingEventsFeed(options?: UseBillingEventsFeedOptions): UseBillingEventsFeedResult {
  const normalizedStatus =
    options?.processingStatus && options.processingStatus !== 'all'
      ? options.processingStatus
      : null;
  const normalizedEventType = options?.eventType?.trim() || null;

  const history = useBillingHistory({
    pageSize: options?.pageSize ?? 25,
    eventType: normalizedEventType,
    processingStatus: normalizedStatus ?? undefined,
  });
  const stream = useBillingStream();

  const filteredStreamEvents = useMemo(() => {
    return stream.events.filter((event) => matchesFilters(event, normalizedStatus, normalizedEventType));
  }, [stream.events, normalizedStatus, normalizedEventType]);

  const mergedEvents = useMemo(
    () => mergeBillingEvents(history.events, filteredStreamEvents),
    [history.events, filteredStreamEvents],
  );

  return {
    events: mergedEvents,
    streamStatus: stream.status,
    isLoading: history.isLoading,
    isFetchingMore: history.isFetchingMore,
    hasNextPage: history.hasNextPage,
    loadMore: history.loadMore,
    refetch: history.refetch,
  };
}

function matchesFilters(
  event: BillingEvent,
  processingStatus: BillingEventProcessingStatus | null,
  eventType: string | null,
): boolean {
  if (processingStatus && event.status !== processingStatus) {
    return false;
  }

  if (eventType && event.event_type !== eventType) {
    return false;
  }

  return true;
}
