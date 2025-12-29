import Link from 'next/link';
import { FileText } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import type { InvoiceSummary } from '@/features/billing/shared/types';

interface InvoiceCardProps {
  summary: InvoiceSummary | null;
  isLoading?: boolean;
}

export function InvoiceCard({ summary, isLoading }: InvoiceCardProps) {
  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">Upcoming Invoice</CardTitle>
        <FileText className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      
      <CardContent className="flex-1 space-y-4">
        {isLoading ? (
          <div className="space-y-2">
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-4 w-16" />
          </div>
        ) : summary ? (
          <>
            <div className="space-y-1">
              <span className="text-2xl font-bold">{summary.amountLabel}</span>
              <div className="flex items-center gap-2">
                <Badge variant="secondary" className="font-normal text-[10px] uppercase tracking-wide">
                  {summary.statusLabel}
                </Badge>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              {summary.reason ?? 'Usage'} · {summary.collectionMethod === 'charge_automatically' ? 'Auto-pay' : 'Invoiced'}
            </p>
          </>
        ) : (
          <div className="flex h-full items-center">
            <p className="text-sm text-muted-foreground">No pending invoice</p>
          </div>
        )}
      </CardContent>

      <CardFooter>
        {summary?.invoiceUrl ? (
          <Button asChild size="sm" variant="outline" className="w-full">
            <Link href={summary.invoiceUrl}>View invoice</Link>
          </Button>
        ) : (
          <Button disabled size="sm" variant="outline" className="w-full">
            No invoice
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
