import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base font-semibold">{title}</CardTitle>
        <InlineTag tone={rows.length ? 'positive' : 'default'}>{`${rows.length} records`}</InlineTag>
      </CardHeader>

      <CardContent className="p-0">
        {showSkeleton ? (
          <div className="p-6">
            <SkeletonPanel lines={4} />
          </div>
        ) : showEmpty ? (
          <div className="p-6">
            <EmptyState title={emptyTitle} description={emptyDescription} />
          </div>
        ) : (
          <div className="border-t">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6">Feature</TableHead>
                  <TableHead className="text-center">Quantity</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right pr-6">Period</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.key}>
                    <TableCell className="pl-6 font-medium">{row.feature}</TableCell>
                    <TableCell className="text-center">{row.quantity}</TableCell>
                    <TableCell className="text-right">{row.amount}</TableCell>
                    <TableCell className="text-right pr-6 text-muted-foreground">{row.period}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              <TableCaption className="pb-4">{caption}</TableCaption>
            </Table>
          </div>
        )}
      </CardContent>

      {ctaHref && ctaLabel ? (
        <CardFooter className="justify-end border-t bg-muted/50 p-3">
          <Button asChild size="sm" variant="ghost">
            <Link href={ctaHref}>{ctaLabel}</Link>
          </Button>
        </CardFooter>
      ) : null}
    </Card>
  );
}
