'use client';

import { Button } from '@/components/ui/button';
import { GlassPanel } from '@/components/ui/foundation';

interface ServiceAccountStatsProps {
  total: number;
  onRefresh: () => void;
  isRefreshing: boolean;
}

export function ServiceAccountStats({ total, onRefresh, isRefreshing }: ServiceAccountStatsProps) {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-sm text-foreground/70">Total tokens</p>
          <p className="text-2xl font-semibold text-foreground">{total}</p>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
          Refresh
        </Button>
      </div>
      <p className="text-sm text-foreground/60">
        Issue tokens directly from this dashboard (browser mode) or provide Vault headers for the compliance-approved issuance flow. Use the table below to audit and revoke credentials at any time.
      </p>
    </GlassPanel>
  );
}
