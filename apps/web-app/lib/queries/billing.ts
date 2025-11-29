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
import { billingEnabled } from '@/lib/config/features';

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
  const [events, setEvents] = useState<BillingEvent[]>([]);
  const [status, setStatus] = useState<BillingStreamStatus>(() => {
    if (!billingEnabled) return 'disabled';
    const meta = readClientSessionMeta();
    if (!meta?.tenantId) return 'disabled';
    return 'connecting';
  });
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (status === 'disabled') return undefined;

    const meta = readClientSessionMeta();
    if (!meta?.tenantId) return undefined;

    // Create abort controller for cleanup
    const controller = new AbortController();
    abortRef.current = controller;

    // Handle new events
    const handleEvent = (event: BillingEvent) => {
      setEvents((previous) => [event, ...previous].slice(0, MAX_EVENTS));
    };

    // Handle status changes
    const handleStatusChange = (newStatus: 'connecting' | 'open' | 'error') => {
      setStatus(newStatus);
    };

    // Connect to stream
    connectBillingStream(handleEvent, handleStatusChange, controller.signal);

    // Cleanup on unmount
    return () => {
      controller.abort();
    };
  }, [status]);

  return { events, status };
}
