import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';
import { formatRelativeTime } from '@/lib/utils/time';

import { BILLING_COPY } from '../constants';
import { formatCurrency, formatStatusLabel, resolveStatusTone } from '../utils/formatters';

interface BillingEventsListProps {
  events: BillingEvent[];
  streamStatus: BillingStreamStatus;
}

export function BillingEventsList({ events, streamStatus }: BillingEventsListProps) {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-foreground">{BILLING_COPY.overview.eventsTitle}</p>
        <InlineTag tone={resolveStatusTone(streamStatus)}>{formatStatusLabel(streamStatus)}</InlineTag>
      </div>

      {events.length === 0 ? (
        <EmptyState title={BILLING_COPY.overview.eventsEmptyTitle} description={BILLING_COPY.overview.eventsEmptyDescription} />
      ) : (
        <ul className="space-y-3 text-sm text-foreground/80">
          {events.slice(0, 5).map((event) => {
            const eventDescription = (() => {
              if (event.invoice) {
                return `Invoice ${event.invoice.invoice_id} · ${formatCurrency(event.invoice.amount_due_cents, event.invoice.currency ?? 'USD')}`;
              }
              if (event.usage?.length) {
                const total = event.usage.reduce((sum, usage) => sum + (usage.quantity ?? 0), 0);
                return `Usage event · ${total} units`;
              }
              return 'System update';
            })();

            return (
              <li key={event.stripe_event_id} className="space-y-2 rounded-xl border border-white/5 bg-white/5 px-4 py-3">
                <div className="flex items-center justify-between gap-3">
                  <p className="font-semibold capitalize">
                    {event.summary ?? event.event_type.replace(/\./g, ' ')}
                  </p>
                  <span className="text-xs text-foreground/50">{formatRelativeTime(event.occurred_at)}</span>
                </div>
                <p className="text-xs text-foreground/60">{eventDescription}</p>
                <InlineTag tone={event.invoice ? 'positive' : 'default'}>
                  {event.event_type.replace(/\./g, ' ')}
                </InlineTag>
              </li>
            );
          })}
        </ul>
      )}

      <div className="flex justify-between text-xs text-foreground/60">
        <span>Showing latest events stream</span>
        <Button asChild size="sm" variant="ghost">
          <Link href="/billing/events">{BILLING_COPY.overview.eventsCtaLabel}</Link>
        </Button>
      </div>
    </GlassPanel>
  );
}
