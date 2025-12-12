'use client';

import { SectionHeader } from '@/components/ui/foundation';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';

import { BILLING_COPY } from './constants';
import { BillingEventsList } from './components/BillingEventsList';
import { InvoiceCard } from './components/InvoiceCard';
import { PlanSnapshotCard } from './components/PlanSnapshotCard';
import { BillingHealthCard } from './components/BillingHealthCard';
import { UsageTable } from './components/UsageTable';
import { useBillingOverviewData } from './hooks/useBillingOverviewData';

export function BillingOverview() {
  const { planSnapshot, usageRows, invoiceSummary, events, streamStatus } = useBillingOverviewData();

  return (
    <section className="space-y-8 max-w-7xl mx-auto">
      <SectionHeader
        eyebrow={BILLING_COPY.overview.eyebrow}
        title={BILLING_COPY.overview.title}
        description={BILLING_COPY.overview.description}
      />

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <PlanSnapshotCard snapshot={planSnapshot} />
        <BillingHealthCard snapshot={planSnapshot} streamStatus={streamStatus} />
        <InvoiceCard summary={invoiceSummary} isLoading={streamStatus === 'connecting'} />
      </div>

      <div className="space-y-6">
        <Tabs defaultValue="usage" className="w-full space-y-6">
          <div className="flex items-center justify-between">
            <TabsList>
              <TabsTrigger value="usage" className="w-32">Usage</TabsTrigger>
              <TabsTrigger value="events" className="w-32">Events</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="usage" className="space-y-4 outline-none">
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
          <TabsContent value="events" className="space-y-4 outline-none">
            <BillingEventsList events={events} streamStatus={streamStatus} />
          </TabsContent>
        </Tabs>
      </div>
    </section>
  );
}
