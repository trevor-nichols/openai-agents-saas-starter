'use client';

import { useMemo } from 'react';
import type { ColumnDef } from '@tanstack/react-table';
import { CheckCircle2, Mail, Network } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states/EmptyState';
import { ErrorState } from '@/components/ui/states/ErrorState';
import { InlineTag } from '@/components/ui/foundation';
import type { StatusSubscriptionSummary } from '@/types/statusSubscriptions';

import { formatDateTime, formatSeverityLabel, resolveStatusTone, formatStatusLabel } from '../utils';

interface SubscriptionsTableProps {
  subscriptions: StatusSubscriptionSummary[];
  isLoading: boolean;
  isError: boolean;
  error?: string;
  skeletonLines?: number;
  onRetry: () => void;
  onRowSelect?: (subscription: StatusSubscriptionSummary) => void;
  selectedId?: string | null;
}

export function SubscriptionsTable({
  subscriptions,
  isLoading,
  isError,
  error,
  skeletonLines = 8,
  onRetry,
  onRowSelect,
  selectedId,
}: SubscriptionsTableProps) {
  const columns: ColumnDef<StatusSubscriptionSummary>[] = useMemo(
    () => [
      {
        id: 'selected',
        header: '',
        cell: ({ row }) =>
          selectedId === row.original.id ? (
            <CheckCircle2 className="h-4 w-4 text-success" aria-label="Selected subscription" />
          ) : null,
        size: 32,
      },
      {
        accessorKey: 'targetMasked',
        header: 'Subscriber',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-mono text-sm text-foreground/90">{row.original.targetMasked}</span>
            <span className="text-xs text-foreground/60">Created by {row.original.createdBy}</span>
          </div>
        ),
      },
      {
        accessorKey: 'channel',
        header: 'Channel',
        cell: ({ row }) => (
          <div className="flex items-center gap-2">
            {row.original.channel === 'email' ? (
              <Mail className="h-4 w-4 text-foreground/70" aria-hidden />
            ) : (
              <Network className="h-4 w-4 text-foreground/70" aria-hidden />
            )}
            <span className="capitalize text-foreground/80">{row.original.channel}</span>
          </div>
        ),
      },
      {
        accessorKey: 'severityFilter',
        header: 'Severity',
        cell: ({ row }) => (
          <Badge variant="outline" className="capitalize">
            {formatSeverityLabel(row.original.severityFilter)}
          </Badge>
        ),
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => (
          <InlineTag tone={resolveStatusTone(row.original.status)}>
            {formatStatusLabel(row.original.status)}
          </InlineTag>
        ),
      },
      {
        accessorKey: 'tenantId',
        header: 'Tenant',
        cell: ({ row }) =>
          row.original.tenantId ? (
            <span className="font-mono text-xs text-foreground/80">{row.original.tenantId}</span>
          ) : (
            <span className="text-xs text-foreground/50">Global</span>
          ),
      },
      {
        accessorKey: 'createdAt',
        header: 'Created',
        cell: ({ row }) => <span className="text-sm text-foreground/70">{formatDateTime(row.original.createdAt)}</span>,
      },
      {
        accessorKey: 'updatedAt',
        header: 'Updated',
        cell: ({ row }) => <span className="text-sm text-foreground/70">{formatDateTime(row.original.updatedAt)}</span>,
      },
    ],
    [selectedId],
  );

  if (isError) {
    return <ErrorState title="Unable to load subscriptions" message={error ?? 'Something went wrong.'} onRetry={onRetry} />;
  }

  const emptyState = (
    <EmptyState
      title="No subscriptions found"
      description="You have not loaded any status alert subscribers yet."
    />
  );

  return (
    <DataTable
      columns={columns}
      data={subscriptions}
      isLoading={isLoading}
      isError={false}
      error={undefined}
      emptyState={emptyState}
      skeletonLines={skeletonLines}
      onRowClick={onRowSelect ? (row) => onRowSelect(row.original) : undefined}
      rowClassName={onRowSelect ? 'cursor-pointer' : undefined}
      enablePagination={false}
    />
  );
}
