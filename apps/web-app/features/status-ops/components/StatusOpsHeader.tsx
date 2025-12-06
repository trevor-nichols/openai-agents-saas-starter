'use client';

import { RefreshCcw } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';

interface StatusOpsHeaderProps {
  onRefresh: () => void;
}

export function StatusOpsHeader({ onRefresh }: StatusOpsHeaderProps) {
  return (
    <SectionHeader
      eyebrow="Operations"
      title="Status console"
      description="Audit status alert subscribers and replay incident notifications without leaving the console."
      actions={
        <div className="flex gap-2">
          <Button variant="outline" onClick={onRefresh}>
            <RefreshCcw className="h-4 w-4" aria-hidden />
            Refresh
          </Button>
        </div>
      }
    />
  );
}
