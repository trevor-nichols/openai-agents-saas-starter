'use client';

import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import { formatRelativeTime } from '@/lib/utils/time';
import type { BillingEvent } from '@/types/billing';

import { BILLING_COPY } from './constants';
import { useBillingOverviewData } from './hooks/useBillingOverviewData';
import { formatCurrency, formatStatusLabel, resolveStatusTone } from './utils/formatters';

const eventsColumns: ColumnDef<BillingEvent>[] = [
  {
    header: 'Occurred',
    accessorKey: 'occurred_at',
    cell: ({ getValue }) => {
      const value = getValue<string>();
      const date = value ? new Date(value) : null;
      return (
        <div className="flex flex-col">
          <span className="font-medium">{date ? date.toLocaleString() : 'Unknown'}</span>
          {value ? <span className="text-xs text-foreground/60">{formatRelativeTime(value)}</span> : null}
        </div>
      );
    },
  },
  {
    header: 'Event',
    accessorKey: 'event_type',
    cell: ({ getValue, row }) => {
      const raw = getValue<string>() ?? 'event';
      const summary = row.original.summary ?? raw.replace(/\./g, ' ');
      return (
        <div>
          <p className="font-semibold capitalize">{raw.replace(/\./g, ' ')}</p>
          <p className="text-sm text-foreground/60">{summary}</p>
        </div>
      );
    },
  },
  {
    header: 'Amount',
    id: 'amount',
    cell: ({ row }) => {
      const invoice = row.original.invoice;
      if (invoice) {
        return formatCurrency(invoice.amount_due_cents, invoice.currency ?? 'USD');
      }
      const usage = row.original.usage;
      if (usage?.length) {
        const total = usage.reduce((sum, entry) => sum + (entry.quantity ?? 0), 0);
        return `${total} units`;
      }
      return '—';
    },
  },
  {
    header: 'Status',
    id: 'status',
    cell: ({ row }) => {
      const status = row.original.subscription?.status ?? row.original.status;
      return <InlineTag tone={resolveStatusTone(status)}>{formatStatusLabel(status)}</InlineTag>;
    },
  },
];

export function EventsLedger() {
  const { events, historyState } = useBillingOverviewData();
  const isInitialLoading = historyState.isLoading && events.length === 0;

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.eventsPage.eyebrow}
        title={BILLING_COPY.eventsPage.title}
        description={BILLING_COPY.eventsPage.description}
      />

      <DataTable
        columns={eventsColumns}
        data={events}
        isLoading={isInitialLoading}
        emptyState={<EmptyState title="No events recorded" description="Stripe events will appear here once billing activity occurs." />}
        enablePagination
      />

      <div className="flex justify-end">
        <Button
          variant="outline"
          onClick={historyState.loadMore}
          disabled={!historyState.hasNextPage || historyState.isFetchingMore}
        >
          {historyState.isFetchingMore
            ? 'Loading…'
            : historyState.hasNextPage
              ? 'Load older events'
              : 'No older events'}
        </Button>
      </div>
    </section>
  );
}
