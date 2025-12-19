'use client';

import { useMemo } from 'react';
import type { ColumnDef } from '@tanstack/react-table';

import { Button } from '@/components/ui/button';
import { DataTable } from '@/components/ui/data-table';
import { EmptyState } from '@/components/ui/states';
import type { AssetResponse } from '@/lib/api/client/types.gen';
import { formatRelativeTime } from '@/lib/utils/time';

import { formatBytes, formatToolLabel } from '../utils/formatters';
import { DeleteAssetDialog } from './DeleteAssetDialog';

interface AssetTableProps {
  assets: AssetResponse[];
  isLoading: boolean;
  error?: string | null;
  onDownload: (asset: AssetResponse) => Promise<void>;
  onDelete: (asset: AssetResponse) => Promise<void>;
  downloadingId?: string | null;
  deletingId?: string | null;
}

export function AssetTable({
  assets,
  isLoading,
  error,
  onDownload,
  onDelete,
  downloadingId,
  deletingId,
}: AssetTableProps) {
  const columns = useMemo<ColumnDef<AssetResponse, unknown>[]>(() => {
    return [
      {
        id: 'name',
        header: 'File',
        cell: ({ row }) => (
          <div className="space-y-1">
            <div className="font-semibold text-foreground">
              {row.original.filename ?? `Asset ${row.original.id.substring(0, 8)}…`}
            </div>
            <div className="text-xs text-foreground/60">
              {row.original.mime_type ?? 'unknown'} • {formatBytes(row.original.size_bytes ?? 0)}
            </div>
          </div>
        ),
      },
      {
        id: 'source',
        header: 'Source',
        cell: ({ row }) => (
          <span className="text-sm text-foreground/70">{formatToolLabel(row.original.source_tool)}</span>
        ),
      },
      {
        id: 'conversation',
        header: 'Conversation',
        cell: ({ row }) => (
          <span className="text-xs text-foreground/60">
            {row.original.conversation_id
              ? row.original.conversation_id.substring(0, 12)
              : '—'}
          </span>
        ),
      },
      {
        id: 'created',
        header: 'Created',
        cell: ({ row }) => (
          <span className="text-xs text-foreground/60">
            {row.original.asset_created_at
              ? formatRelativeTime(row.original.asset_created_at)
              : '—'}
          </span>
        ),
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => {
          const asset = row.original;
          const isDownloading = downloadingId === asset.id;
          const isDeleting = deletingId === asset.id;
          return (
            <div className="flex items-center justify-end gap-2">
              <Button
                size="sm"
                variant="secondary"
                disabled={isDownloading}
                onClick={() => onDownload(asset)}
              >
                {isDownloading ? 'Fetching…' : 'Download'}
              </Button>
              <DeleteAssetDialog
                assetLabel={asset.filename ?? 'this asset'}
                isPending={isDeleting}
                onConfirm={() => onDelete(asset)}
              >
                <Button size="sm" variant="ghost" disabled={isDeleting}>
                  Delete
                </Button>
              </DeleteAssetDialog>
            </div>
          );
        },
      },
    ];
  }, [deletingId, downloadingId, onDelete, onDownload]);

  return (
    <DataTable
      columns={columns}
      data={assets}
      className="rounded-2xl border border-white/10 bg-white/5"
      isLoading={isLoading}
      isError={Boolean(error)}
      error={error ?? undefined}
      emptyState={
        <EmptyState
          title="No files found"
          description="Generate a file or adjust your filters."
        />
      }
      enableSorting={false}
      enablePagination={false}
    />
  );
}
