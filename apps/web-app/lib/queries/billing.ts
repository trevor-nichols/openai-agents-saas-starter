/**
 * Billing stream hook
 *
 * Note: This uses a custom hook pattern rather than TanStack Query
 * because SSE streams are long-lived connections, not request-response queries.
 * TanStack Query is optimized for cacheable request-response patterns.
 */

'use client';

import { useEffect, useRef, useState } from 'react';

import type { BillingEvent, BillingStreamStatus } from '@/types/billing';
import { readClientSessionMeta } from '@/lib/auth/clientMeta';
import { connectBillingStream } from '@/lib/api/billing';
import { useFeatureFlags } from '@/lib/queries/featureFlags';

const MAX_EVENTS = 20;

interface UseBillingStreamReturn {
  events: BillingEvent[];
  status: BillingStreamStatus;
}

/**
 * Hook to manage real-time billing event stream
 *
 * Features:
 * - Automatic connection management
 * - Keeps last 20 events
 * - Proper cleanup on unmount
 * - Status tracking
 */
export function useBillingStream(): UseBillingStreamReturn {
  const { flags, isLoading } = useFeatureFlags();
  const billingEnabled = Boolean(flags?.billingEnabled);
  const billingStreamEnabled = Boolean(flags?.billingStreamEnabled);
  const meta = readClientSessionMeta();
  const canStream = Boolean(
    !isLoading && billingEnabled && billingStreamEnabled && meta?.tenantId
  );
  const [events, setEvents] = useState<BillingEvent[]>([]);
  const [streamStatus, setStreamStatus] = useState<
    Exclude<BillingStreamStatus, 'disabled'>
  >('connecting');
  const abortRef = useRef<AbortController | null>(null);
  const status: BillingStreamStatus = canStream ? streamStatus : 'disabled';

  useEffect(() => {
    if (!canStream) return undefined;

    // Create abort controller for cleanup
    const controller = new AbortController();
    abortRef.current = controller;

    // Handle new events
    const handleEvent = (event: BillingEvent) => {
      setEvents((previous) => [event, ...previous].slice(0, MAX_EVENTS));
    };

    // Handle status changes
    const handleStatusChange = (newStatus: 'connecting' | 'open' | 'error') => {
      setStreamStatus(newStatus);
    };

    // Connect to stream
    void connectBillingStream(handleEvent, handleStatusChange, controller.signal);

    // Cleanup on unmount
    return () => {
      controller.abort();
    };
  }, [canStream]);

  return { events, status };
}
