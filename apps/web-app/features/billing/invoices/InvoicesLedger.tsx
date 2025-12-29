'use client';

import Link from 'next/link';
import { useMemo } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';
import { useBillingInvoices } from '@/lib/queries/billingInvoices';
import type { BillingInvoice } from '@/types/billing';

import { BILLING_COPY } from '../shared/constants';
import { formatCurrency, formatPeriod, formatStatusLabel, resolveStatusTone } from '../shared/utils/formatters';

const invoiceColumns: ColumnDef<BillingInvoice>[] = [
  {
    header: 'Invoice',
    accessorKey: 'invoice_id',
    cell: ({ row }) => {
      const invoice = row.original;
      const label = invoice.invoice_id ?? 'Invoice';
      const url = invoice.hosted_invoice_url ?? null;
      if (url) {
        return (
          <Link href={url} className="font-medium hover:underline" target="_blank" rel="noreferrer">
            {label}
          </Link>
        );
      }
      return <span className="font-medium">{label}</span>;
    },
  },
  {
    header: 'Period',
    accessorKey: 'period_start',
    cell: ({ row }) => formatPeriod(row.original.period_start, row.original.period_end),
  },
  {
    header: 'Amount',
    accessorKey: 'amount_cents',
    cell: ({ row }) => (
      <span className="text-right">
        {formatCurrency(row.original.amount_cents, row.original.currency ?? 'USD')}
      </span>
    ),
  },
  {
    header: 'Status',
    accessorKey: 'status',
    cell: ({ row }) => (
      <InlineTag tone={resolveStatusTone(row.original.status)}>
        {formatStatusLabel(row.original.status)}
      </InlineTag>
    ),
  },
];

export function InvoicesLedger() {
  const {
    invoices,
    isLoading,
    isFetchingMore,
    hasNextPage,
    loadMore,
    error,
  } = useBillingInvoices({ pageSize: 25 });

  const rows = useMemo(() => invoices, [invoices]);

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.invoicesPage.eyebrow}
        title={BILLING_COPY.invoicesPage.title}
        description={BILLING_COPY.invoicesPage.description}
      />

      <DataTable
        columns={invoiceColumns}
        data={rows}
        isLoading={isLoading}
        isError={Boolean(error)}
        error={error?.message}
        emptyState={
          <EmptyState
            title="No invoices recorded"
            description="Stored invoices will appear here once billing cycles complete."
          />
        }
        enablePagination
      />

      <div className="flex justify-end">
        <Button
          variant="outline"
          onClick={loadMore}
          disabled={!hasNextPage || isFetchingMore}
        >
          {isFetchingMore
            ? 'Loading…'
            : hasNextPage
              ? 'Load older invoices'
              : 'No older invoices'}
        </Button>
      </div>
    </section>
  );
}
