'use client';

import { SectionHeader, InlineTag } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

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
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.overview.eyebrow}
        title={BILLING_COPY.overview.title}
        description={BILLING_COPY.overview.description}
        actions={
          <InlineTag tone={resolveStatusTone(streamStatus)}>{formatStatusLabel(streamStatus)}</InlineTag>
        }
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <Tabs defaultValue="usage" className="space-y-4">
            <TabsList className="w-full max-w-md">
              <TabsTrigger value="usage">Usage</TabsTrigger>
              <TabsTrigger value="events">Events</TabsTrigger>
            </TabsList>
            <TabsContent value="usage" className="space-y-4">
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
            </TabsContent>
            <TabsContent value="events" className="space-y-4">
              <BillingEventsList events={events} streamStatus={streamStatus} />
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-4">
          <PlanSnapshotCard snapshot={planSnapshot} streamStatus={streamStatus} />
          <InvoiceCard summary={invoiceSummary} isLoading={streamStatus === 'connecting'} />
        </div>
      </div>
    </section>
  );
}
