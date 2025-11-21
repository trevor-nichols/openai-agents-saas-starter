import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { GlassPanel } from '@/components/ui/foundation';
import { SkeletonPanel } from '@/components/ui/states';
import type { InvoiceSummary } from '@/features/billing/types';

interface InvoiceCardProps {
  summary: InvoiceSummary | null;
  isLoading?: boolean;
}

export function InvoiceCard({ summary, isLoading }: InvoiceCardProps) {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Upcoming invoice</p>
          <p className="text-lg font-semibold text-foreground">{summary?.amountLabel ?? '—'}</p>
        </div>
        <Badge variant="outline">{summary?.statusLabel ?? 'pending'}</Badge>
      </div>

      {isLoading ? (
        <SkeletonPanel lines={4} />
      ) : summary ? (
        <div className="space-y-2 text-sm text-foreground/70">
          <p>
            <strong>Reason:</strong> {summary.reason ?? 'Usage'}
          </p>
          <p>
            <strong>Collection:</strong> {summary.collectionMethod ?? 'auto'}
          </p>
          <div className="flex flex-wrap gap-2">
            {summary.invoiceUrl ? (
              <Button asChild size="sm">
                <Link href={summary.invoiceUrl}>View invoice</Link>
              </Button>
            ) : null}
            <Button asChild size="sm" variant="ghost">
              <Link href="/billing/plans">Manage plan</Link>
            </Button>
          </div>
        </div>
      ) : null}
    </GlassPanel>
  );
}
