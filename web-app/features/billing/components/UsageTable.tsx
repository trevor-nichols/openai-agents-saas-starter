import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { EmptyState, SkeletonPanel } from '@/components/ui/states';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { UsageRow } from '@/features/billing/types';

interface UsageTableProps {
  title: string;
  rows: UsageRow[];
  emptyTitle: string;
  emptyDescription: string;
  ctaHref?: string;
  ctaLabel?: string;
  caption?: string;
  showSkeleton?: boolean;
}

export function UsageTable({
  title,
  rows,
  emptyTitle,
  emptyDescription,
  ctaHref,
  ctaLabel,
  caption = 'Mirror this table with your own billing pipeline.',
  showSkeleton,
}: UsageTableProps) {
  const showEmpty = !showSkeleton && rows.length === 0;

  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-foreground">{title}</p>
        <InlineTag tone={rows.length ? 'positive' : 'default'}>{`${rows.length} records`}</InlineTag>
      </div>

      {showSkeleton ? (
        <SkeletonPanel lines={4} />
      ) : showEmpty ? (
        <EmptyState title={emptyTitle} description={emptyDescription} />
      ) : (
        <Table className="text-xs">
          <TableHeader>
            <TableRow>
              <TableHead>Feature</TableHead>
              <TableHead className="text-center">Quantity</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">Period</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.map((row) => (
              <TableRow key={row.key}>
                <TableCell>{row.feature}</TableCell>
                <TableCell className="text-center">{row.quantity}</TableCell>
                <TableCell className="text-right">{row.amount}</TableCell>
                <TableCell className="text-right">{row.period}</TableCell>
              </TableRow>
            ))}
          </TableBody>
          <TableCaption>{caption}</TableCaption>
        </Table>
      )}

      {ctaHref && ctaLabel ? (
        <div className="flex justify-end">
          <Button asChild size="sm" variant="outline">
            <Link href={ctaHref}>{ctaLabel}</Link>
          </Button>
        </div>
      ) : null}
    </GlassPanel>
  );
}
