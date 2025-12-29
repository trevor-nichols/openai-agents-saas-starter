'use client';

import { FileText } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import { useUpcomingInvoicePreview } from '@/lib/queries/billingUpcomingInvoice';
import type { UpcomingInvoicePreview } from '@/types/billing';

import { BILLING_COPY } from '../../shared/constants';
import { formatCurrency, formatPeriod } from '../../shared/utils/formatters';

interface UpcomingInvoicePreviewCardProps {
  tenantId: string | null;
  seatCount?: number | null;
  enabled?: boolean;
}

export function UpcomingInvoicePreviewCard({
  tenantId,
  seatCount,
  enabled = true,
}: UpcomingInvoicePreviewCardProps) {
  const { preview, isLoading, error, refetch } = useUpcomingInvoicePreview({
    tenantId,
    seatCount,
    enabled,
  });

  return (
    <UpcomingInvoicePreviewCardContent
      preview={preview}
      isLoading={isLoading}
      error={error}
      onRetry={refetch}
      enabled={enabled}
    />
  );
}

interface UpcomingInvoicePreviewCardContentProps {
  preview: UpcomingInvoicePreview | null;
  isLoading: boolean;
  error: string | null;
  onRetry: () => void;
  enabled?: boolean;
}

export function UpcomingInvoicePreviewCardContent({
  preview,
  isLoading,
  error,
  onRetry,
  enabled = true,
}: UpcomingInvoicePreviewCardContentProps) {
  if (!enabled) {
    return (
      <GlassPanel>
        <EmptyState
          title={BILLING_COPY.planManagement.invoicePreview.emptyTitle}
          description={BILLING_COPY.planManagement.invoicePreview.emptyDescription}
        />
      </GlassPanel>
    );
  }

  if (isLoading) {
    return (
      <GlassPanel>
        <SkeletonPanel lines={3} />
      </GlassPanel>
    );
  }

  if (error) {
    return (
      <GlassPanel>
        <ErrorState title="Unable to load invoice preview" message={error} onRetry={onRetry} />
      </GlassPanel>
    );
  }

  if (!preview) {
    return (
      <GlassPanel>
        <EmptyState
          title={BILLING_COPY.planManagement.invoicePreview.emptyTitle}
          description={BILLING_COPY.planManagement.invoicePreview.emptyDescription}
        />
      </GlassPanel>
    );
  }

  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-start justify-between gap-4">
        <div className="space-y-1">
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">
            {BILLING_COPY.planManagement.invoicePreview.title}
          </p>
          <p className="text-2xl font-semibold text-foreground">
            {formatCurrency(preview.amount_due_cents, preview.currency)}
          </p>
          <p className="text-sm text-foreground/60">
            {preview.plan_name} · {preview.seat_count ?? '—'} seats
          </p>
        </div>
        <InlineTag tone="default" className="flex items-center gap-2">
          <FileText className="h-3.5 w-3.5" />
          Preview
        </InlineTag>
      </div>

      <div className="text-xs text-foreground/60">
        Billing period · {formatPeriod(preview.period_start, preview.period_end)}
      </div>

      {preview.lines && preview.lines.length > 0 ? (
        <div className="rounded-xl border border-white/5 bg-white/5">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Description</TableHead>
                <TableHead className="text-right">Amount</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {preview.lines.map((line, index) => (
                <TableRow key={`${line.price_id ?? 'line'}-${index}`}>
                  <TableCell>
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">
                        {line.description ?? 'Charge'}
                      </p>
                      {line.quantity ? (
                        <p className="text-xs text-foreground/60">
                          Qty {line.quantity}
                          {line.unit_amount_cents
                            ? ` · ${formatCurrency(line.unit_amount_cents, line.currency ?? preview.currency)} each`
                            : ''}
                        </p>
                      ) : null}
                    </div>
                  </TableCell>
                  <TableCell className="text-right">
                    {formatCurrency(line.amount_cents, line.currency ?? preview.currency)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <p className="text-sm text-foreground/60">No line items available.</p>
      )}

      <Button variant="outline" size="sm" onClick={onRetry} className="w-full">
        Refresh preview
      </Button>
    </GlassPanel>
  );
}
