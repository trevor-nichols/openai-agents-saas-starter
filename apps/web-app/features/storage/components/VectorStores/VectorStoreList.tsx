'use client';

import { Button } from '@/components/ui/button';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import type { VectorStoreListResponse } from '@/lib/api/client/types.gen';

interface VectorStoreListProps {
  items: VectorStoreListResponse['items'];
  selectedId: string | null;
  isLoading: boolean;
  isError: boolean;
  errorMessage?: string;
  isDeleting: boolean;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
}

export function VectorStoreList({
  items,
  selectedId,
  isLoading,
  isError,
  errorMessage,
  isDeleting,
  onSelect,
  onDelete,
}: VectorStoreListProps) {
  if (isLoading) {
    return <SkeletonPanel lines={6} />;
  }

  if (isError) {
    return <ErrorState title="Failed to load vector stores" message={errorMessage} />;
  }

  if (!items.length) {
    return <EmptyState title="No vector stores" description="Create a store to attach files." />;
  }

  return (
    <div className="grid gap-2">
      {items.map((vs) => (
        <div
          key={vs.id}
          className="rounded-lg border border-white/5 bg-white/5 p-3 flex items-center justify-between gap-3"
        >
          <div>
            <div className="font-semibold">{vs.name}</div>
            <div className="text-xs text-foreground/60">{vs.description ?? '—'}</div>
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant={selectedId === vs.id ? 'default' : 'secondary'}
              onClick={() => onSelect(vs.id)}
            >
              {selectedId === vs.id ? 'Selected' : 'Files'}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => onDelete(vs.id)} disabled={isDeleting}>
              Delete
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
