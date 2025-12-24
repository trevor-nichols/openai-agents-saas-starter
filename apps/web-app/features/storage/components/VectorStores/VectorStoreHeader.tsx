'use client';

import { Button } from '@/components/ui/button';

interface VectorStoreHeaderProps {
  isRefreshing: boolean;
  onRefresh: () => void;
}

export function VectorStoreHeader({ isRefreshing, onRefresh }: VectorStoreHeaderProps) {
  return (
    <div className="flex items-center justify-between">
      <div>
        <h3 className="text-sm font-semibold">Vector Stores</h3>
        <p className="text-xs text-foreground/60">Create stores and attach uploaded files.</p>
      </div>
      <Button size="sm" variant="outline" onClick={onRefresh} disabled={isRefreshing}>
        Refresh
      </Button>
    </div>
  );
}
