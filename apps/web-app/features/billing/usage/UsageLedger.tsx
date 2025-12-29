'use client';

import type { ColumnDef } from '@tanstack/react-table';

import { SectionHeader } from '@/components/ui/foundation';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';

import { BILLING_COPY } from '../shared/constants';
import { useBillingOverviewData } from '../shared/hooks/useBillingOverviewData';
import type { UsageRow } from '../shared/types';

const usageColumns: ColumnDef<UsageRow>[] = [
  {
    header: 'Feature',
    accessorKey: 'feature',
  },
  {
    header: 'Quantity',
    accessorKey: 'quantity',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
  {
    header: 'Amount',
    accessorKey: 'amount',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
  {
    header: 'Period',
    accessorKey: 'period',
    cell: ({ getValue }) => <span className="text-right">{getValue<string>()}</span>,
  },
];

export function UsageLedger() {
  const { allUsageRows } = useBillingOverviewData();

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.usagePage.eyebrow}
        title={BILLING_COPY.usagePage.title}
        description={BILLING_COPY.usagePage.description}
      />

      <DataTable
        columns={usageColumns}
        data={allUsageRows}
        emptyState={
          <EmptyState
            title="No usage recorded"
            description="Metered features will populate this ledger once they emit events."
          />
        }
        enablePagination
      />
    </section>
  );
}
