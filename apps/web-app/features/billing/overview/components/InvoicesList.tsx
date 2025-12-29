import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { InlineTag } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import type { BillingInvoice } from '@/types/billing';

import { BILLING_COPY } from '../../shared/constants';
import { formatCurrency, formatPeriod, formatStatusLabel, resolveStatusTone } from '../../shared/utils/formatters';

interface InvoicesListProps {
  invoices: BillingInvoice[];
  isLoading?: boolean;
  errorMessage?: string;
}

export function InvoicesList({ invoices, isLoading, errorMessage }: InvoicesListProps) {
  const showEmpty = !isLoading && invoices.length === 0 && !errorMessage;
  const showError = !isLoading && Boolean(errorMessage);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
        <CardTitle className="text-base font-semibold">{BILLING_COPY.overview.invoicesTitle}</CardTitle>
        <InlineTag tone={invoices.length ? 'positive' : 'default'}>{`${invoices.length} invoices`}</InlineTag>
      </CardHeader>

      <CardContent className="p-0">
        {isLoading ? (
          <div className="p-6">
            <SkeletonPanel lines={4} />
          </div>
        ) : showError ? (
          <div className="p-6">
            <ErrorState title="Unable to load invoices" message={errorMessage} />
          </div>
        ) : showEmpty ? (
          <div className="p-6">
            <EmptyState title={BILLING_COPY.overview.invoicesEmptyTitle} description={BILLING_COPY.overview.invoicesEmptyDescription} />
          </div>
        ) : (
          <div className="border-t">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="pl-6">Invoice</TableHead>
                  <TableHead>Period</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right pr-6">Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {invoices.map((invoice, index) => {
                  const label = invoice.invoice_id ?? `Invoice ${index + 1}`;
                  const url = invoice.hosted_invoice_url ?? null;
                  return (
                    <TableRow key={`${invoice.invoice_id ?? 'invoice'}-${index}`}>
                      <TableCell className="pl-6 font-medium">
                        {url ? (
                          <Link href={url} className="hover:underline" target="_blank" rel="noreferrer">
                            {label}
                          </Link>
                        ) : (
                          label
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatPeriod(invoice.period_start, invoice.period_end)}
                      </TableCell>
                      <TableCell className="text-right">
                        {formatCurrency(invoice.amount_cents, invoice.currency ?? 'USD')}
                      </TableCell>
                      <TableCell className="text-right pr-6">
                        <InlineTag tone={resolveStatusTone(invoice.status)}>
                          {formatStatusLabel(invoice.status)}
                        </InlineTag>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>

      <CardFooter className="justify-end border-t bg-muted/50 p-3">
        <Button asChild size="sm" variant="ghost">
          <Link href="/billing/invoices">{BILLING_COPY.overview.invoicesCtaLabel}</Link>
        </Button>
      </CardFooter>
    </Card>
  );
}
