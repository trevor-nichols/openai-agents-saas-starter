import type { BillingEvent } from '@/types/billing';

/**
 * Merge live stream events with paged history, deduplicating by Stripe event id
 * and ordering by newest occurrence first.
 */
export function mergeBillingEvents(history: BillingEvent[], stream: BillingEvent[]): BillingEvent[] {
  const seen = new Map<string, BillingEvent>();
  const combined = [...stream, ...history];

  for (const event of combined) {
    const key = event.stripe_event_id;
    if (!seen.has(key)) {
      seen.set(key, event);
    }
  }

  return Array.from(seen.values()).sort((a, b) => {
    return new Date(b.occurred_at).getTime() - new Date(a.occurred_at).getTime();
  });
}
