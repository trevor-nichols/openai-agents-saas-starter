import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import type { BillingEvent, BillingStreamStatus } from '@/types/billing';
import { formatRelativeTime } from '@/lib/utils/time';

import { BILLING_COPY } from '../../shared/constants';
import { formatCurrency, formatStatusLabel, resolveStatusTone } from '../../shared/utils/formatters';

interface BillingEventsListProps {
  events: BillingEvent[];
  streamStatus: BillingStreamStatus;
}

export function BillingEventsList({ events, streamStatus }: BillingEventsListProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base font-semibold">{BILLING_COPY.overview.eventsTitle}</CardTitle>
        <InlineTag tone={resolveStatusTone(streamStatus)}>{formatStatusLabel(streamStatus)}</InlineTag>
      </CardHeader>

      <CardContent className="p-0">
        {events.length === 0 ? (
          <div className="p-6">
            <EmptyState title={BILLING_COPY.overview.eventsEmptyTitle} description={BILLING_COPY.overview.eventsEmptyDescription} />
          </div>
        ) : (
          <ul className="divide-y border-t">
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
                <li key={event.stripe_event_id} className="flex items-center justify-between px-6 py-4 hover:bg-muted/30 transition-colors">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                        <p className="text-sm font-medium capitalize">
                            {event.summary ?? event.event_type.replace(/\./g, ' ')}
                        </p>
                        <InlineTag tone={event.invoice ? 'positive' : 'default'} className="h-5 text-[10px] px-1.5 py-0">
                            {event.event_type.replace(/\./g, ' ')}
                        </InlineTag>
                    </div>
                    <p className="text-xs text-muted-foreground">{eventDescription}</p>
                  </div>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">{formatRelativeTime(event.occurred_at)}</span>
                </li>
              );
            })}
          </ul>
        )}
      </CardContent>

      <CardFooter className="justify-between border-t bg-muted/50 p-3">
        <span className="text-xs text-muted-foreground ml-2">Showing latest events stream</span>
        <Button asChild size="sm" variant="ghost">
          <Link href="/billing/events">{BILLING_COPY.overview.eventsCtaLabel}</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
