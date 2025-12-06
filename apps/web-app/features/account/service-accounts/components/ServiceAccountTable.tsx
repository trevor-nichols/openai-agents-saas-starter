'use client';

import { useMemo } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState } from '@/components/ui/states';
import type { ServiceAccountTokenRow } from '@/types/serviceAccounts';

import { formatDate, resolveTokenStatus } from '../utils/display';

interface ServiceAccountTableProps {
  tokens: ServiceAccountTokenRow[];
  isLoading: boolean;
  onRevoke: (token: ServiceAccountTokenRow) => void;
  disableRevoke: boolean;
}

export function ServiceAccountTable({ tokens, isLoading, onRevoke, disableRevoke }: ServiceAccountTableProps) {
  const columns = useMemo<ColumnDef<ServiceAccountTokenRow>[]>(
    () => [
      {
        header: 'Account',
        cell: ({ row }) => (
          <div className="flex flex-col">
            <span className="font-medium text-foreground">{row.original.account}</span>
            <span className="text-xs text-foreground/60">{row.original.fingerprint || row.original.id}</span>
          </div>
        ),
      },
      {
        header: 'Scopes',
        cell: ({ row }) => (
          <div className="flex flex-wrap gap-1">
            {row.original.scopes.map((scope) => (
              <InlineTag key={scope} tone="default">
                {scope}
              </InlineTag>
            ))}
          </div>
        ),
      },
      {
        header: 'Lifecycle',
        cell: ({ row }) => (
          <div className="flex flex-col text-sm">
            <span>Issued {formatDate(row.original.issuedAt)}</span>
            <span className="text-xs text-foreground/60">Expires {formatDate(row.original.expiresAt)}</span>
          </div>
        ),
      },
      {
        header: 'Status',
        cell: ({ row }) => {
          const status = resolveTokenStatus(row.original);
          return <InlineTag tone={status.tone}>{status.label}</InlineTag>;
        },
      },
      {
        id: 'actions',
        header: 'Actions',
        cell: ({ row }) => (
          <Button
            size="sm"
            variant="outline"
            disabled={row.original.revokedAt !== null || disableRevoke}
            onClick={() => onRevoke(row.original)}
          >
            Revoke
          </Button>
        ),
      },
    ],
    [disableRevoke, onRevoke],
  );

  return (
    <DataTable<ServiceAccountTokenRow>
      columns={columns}
      data={tokens}
      isLoading={isLoading}
      emptyState={<EmptyState title="No service-account tokens" description="Issue a token via the Starter CLI to see it here." />}
    />
  );
}
