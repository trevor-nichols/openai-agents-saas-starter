import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { UsageRow } from '../types';

interface UsageTableProps {
  title: string;
  rows: UsageRow[];
  emptyTitle: string;
  emptyDescription: string;
  ctaHref?: string;
  ctaLabel?: string;
  caption?: string;
  showSkeleton?: boolean;
  errorMessage?: string;
  windowLabel?: string;
  quantityLabel?: string;
  amountLabel?: string;
  periodLabel?: string;
  showAmount?: boolean;
  countLabel?: string;
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
  errorMessage,
  windowLabel,
  quantityLabel = 'Quantity',
  amountLabel = 'Amount',
  periodLabel = 'Period',
  showAmount = true,
  countLabel = 'records',
}: UsageTableProps) {
  const showEmpty = !showSkeleton && rows.length === 0;
  const showError = !showSkeleton && Boolean(errorMessage);

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-4">
        <div className="space-y-1">
          <CardTitle className="text-base font-semibold">{title}</CardTitle>
          {windowLabel ? (
            <CardDescription className="text-xs text-muted-foreground">
              {windowLabel}
            </CardDescription>
          ) : null}
        </div>
        <InlineTag tone={rows.length ? 'positive' : 'default'}>{`${rows.length} ${countLabel}`}</InlineTag>
      </CardHeader>

      <CardContent className="p-0">
        {showSkeleton ? (
          <div className="p-6">
            <SkeletonPanel lines={4} />
          </div>
        ) : showError ? (
          <div className="p-6">
            <ErrorState title="Unable to load usage totals" message={errorMessage} />
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
                  <TableHead className="text-center">{quantityLabel}</TableHead>
                  {showAmount ? (
                    <TableHead className="text-right">{amountLabel}</TableHead>
                  ) : null}
                  <TableHead className="text-right pr-6">{periodLabel}</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow key={row.key}>
                    <TableCell className="pl-6 font-medium">{row.feature}</TableCell>
                    <TableCell className="text-center">{row.quantity}</TableCell>
                    {showAmount ? (
                      <TableCell className="text-right">{row.amount}</TableCell>
                    ) : null}
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
