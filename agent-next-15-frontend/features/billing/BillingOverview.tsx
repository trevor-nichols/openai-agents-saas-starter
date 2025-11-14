'use client';

import { SectionHeader, InlineTag } from '@/components/ui/foundation';

import { BILLING_COPY } from './constants';
import { BillingEventsList } from './components/BillingEventsList';
import { InvoiceCard } from './components/InvoiceCard';
import { PlanSnapshotCard } from './components/PlanSnapshotCard';
import { UsageTable } from './components/UsageTable';
import { useBillingOverviewData } from './hooks/useBillingOverviewData';
import { formatStatusLabel, resolveStatusTone } from './utils/formatters';

export function BillingOverview() {
  const { planSnapshot, usageRows, invoiceSummary, events, streamStatus } = useBillingOverviewData();

  return (
    <section className="space-y-10">
      <SectionHeader
        eyebrow={BILLING_COPY.overview.eyebrow}
        title={BILLING_COPY.overview.title}
        description={BILLING_COPY.overview.description}
        actions={
          <InlineTag tone={resolveStatusTone(streamStatus)}>{formatStatusLabel(streamStatus)}</InlineTag>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_0.6fr]">
        <div className="space-y-6">
          <PlanSnapshotCard snapshot={planSnapshot} streamStatus={streamStatus} />
          <UsageTable
            title={BILLING_COPY.overview.usageTableTitle}
            rows={usageRows}
            emptyTitle={BILLING_COPY.overview.usageTableEmptyTitle}
            emptyDescription={BILLING_COPY.overview.usageTableEmptyDescription}
            ctaHref="/billing/usage"
            ctaLabel={BILLING_COPY.overview.usageCtaLabel}
            caption="Mirror this table with your own billing pipeline."
            showSkeleton={streamStatus === 'connecting'}
          />
        </div>

        <div className="space-y-6">
          <InvoiceCard summary={invoiceSummary} isLoading={streamStatus === 'connecting'} />
          <BillingEventsList events={events} streamStatus={streamStatus} />
        </div>
      </div>
    </section>
  );
}
