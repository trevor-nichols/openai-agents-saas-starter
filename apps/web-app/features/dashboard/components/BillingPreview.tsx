import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, KeyValueList, SectionHeader } from '@/components/ui/foundation';
import { Separator } from '@/components/ui/separator';
import { formatRelativeTime } from '@/lib/utils/time';

import { DASHBOARD_COPY } from '../constants';
import type { BillingPreviewSummary } from '../types';
import { formatCurrency } from '../utils/formatters';

interface BillingPreviewProps {
  preview: BillingPreviewSummary;
}

function resolveBadgeVariant(status: string) {
  if (!status) return 'secondary';
  if (['active', 'open', 'trialing'].includes(status)) {
    return 'default'; // or a specific success variant if available, default usually works
  }
  if (['past_due', 'canceled', 'error'].includes(status)) {
    return 'destructive';
  }
  return 'secondary';
}

export function BillingPreview({ preview }: BillingPreviewProps) {
  const { planCode, planStatus, streamStatus, nextInvoiceLabel, latestEvents } = preview;

  return (
    <GlassPanel className="flex h-full flex-col space-y-6">
      <SectionHeader
        eyebrow={DASHBOARD_COPY.billingPreview.eyebrow}
        title={DASHBOARD_COPY.billingPreview.title}
        description={DASHBOARD_COPY.billingPreview.description}
        actions={
          <Button asChild size="sm" variant="ghost">
            <Link href="/billing">{DASHBOARD_COPY.billingPreview.ctaLabel}</Link>
          </Button>
        }
      />

      <div className="space-y-6">
        <div className="flex items-center justify-between rounded-lg border border-white/5 bg-white/5 p-4">
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">Current Plan</p>
              <p className="mt-1 text-lg font-semibold text-foreground">{planCode}</p>
            </div>
            <Badge variant={resolveBadgeVariant(planStatus)} className="uppercase">
              {planStatus}
            </Badge>
        </div>

        <KeyValueList
          items={[
            {
              label: 'Stream Status',
              value: (
                <div className="flex items-center gap-2">
                   <div className={`h-2 w-2 rounded-full ${streamStatus === 'open' ? 'bg-green-500' : 'bg-red-500'}`} />
                   <span className="capitalize">{streamStatus}</span>
                </div>
              ),
            },
            {
              label: 'Next Invoice',
              value: nextInvoiceLabel || '—',
              hint: nextInvoiceLabel ? 'Estimated amount' : undefined,
            },
          ]}
          columns={1}
        />

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Latest Events</p>
          {latestEvents.length === 0 ? (
            <div className="rounded-lg border border-dashed border-white/10 px-4 py-6 text-center text-xs text-muted-foreground">
              {DASHBOARD_COPY.billingPreview.emptyEvents}
            </div>
          ) : (
            <div className="space-y-3">
              {latestEvents.map((event, i) => (
                <div key={event.stripe_event_id}>
                  <div className="flex flex-col gap-1 text-sm">
                    <div className="flex justify-between gap-2">
                      <span className="font-medium text-foreground truncate">
                        {event.summary ?? event.event_type}
                      </span>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {formatRelativeTime(event.occurred_at)}
                      </span>
                    </div>
                    {event.invoice?.amount_due_cents ? (
                      <span className="text-xs text-muted-foreground">
                        {formatCurrency(event.invoice.amount_due_cents, event.invoice.currency ?? 'USD')}
                      </span>
                    ) : null}
                  </div>
                  {i < latestEvents.length - 1 && <Separator className="mt-3 bg-white/5" />}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </GlassPanel>
  );
}
