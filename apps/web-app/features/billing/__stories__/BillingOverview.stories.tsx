'use client';

import type { Meta, StoryObj } from '@storybook/react';
import { useMemo, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { InlineTag, SectionHeader } from '@/components/ui/foundation';

import { BILLING_COPY } from '../constants';
import { BillingEventsList } from '../components/BillingEventsList';
import { InvoiceCard } from '../components/InvoiceCard';
import { PlanSnapshotCard } from '../components/PlanSnapshotCard';
import { UsageTable } from '../components/UsageTable';
import type { BillingStreamStatus } from '@/types/billing';
import { mockBillingEvents, mockInvoiceSummary, mockPlanSnapshot, mockUsageRows } from './fixtures';

type BillingOverviewPreviewProps = {
  streamStatus?: BillingStreamStatus;
  showEmpty?: boolean;
};

function BillingOverviewPreview({ streamStatus = 'open', showEmpty = false }: BillingOverviewPreviewProps) {
  const [tab, setTab] = useState<'usage' | 'events'>('usage');

  const usageRows = useMemo(() => (showEmpty ? [] : mockUsageRows), [showEmpty]);
  const events = useMemo(() => (showEmpty ? [] : mockBillingEvents), [showEmpty]);
  const invoice = useMemo(() => (showEmpty ? null : mockInvoiceSummary), [showEmpty]);
  const snapshot = mockPlanSnapshot;

  const showSkeleton = streamStatus === 'connecting';

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={BILLING_COPY.overview.eyebrow}
        title={BILLING_COPY.overview.title}
        description={BILLING_COPY.overview.description}
        actions={<InlineTag tone={snapshot.statusTone}>{streamStatus}</InlineTag>}
      />

      <div className="grid gap-6 lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_380px]">
        <div className="space-y-4">
          <Tabs value={tab} onValueChange={(value) => setTab(value as typeof tab)} className="space-y-4">
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
                showSkeleton={showSkeleton}
              />
            </TabsContent>
            <TabsContent value="events" className="space-y-4">
              <BillingEventsList events={events} streamStatus={streamStatus} />
            </TabsContent>
          </Tabs>
        </div>

        <div className="space-y-4">
          <PlanSnapshotCard snapshot={snapshot} />
          <InvoiceCard summary={invoice} isLoading={showSkeleton} />
        </div>
      </div>
    </section>
  );
}

const meta: Meta<typeof BillingOverviewPreview> = {
  title: 'Billing/OverviewPage',
  component: BillingOverviewPreview,
};

export default meta;

type Story = StoryObj<typeof BillingOverviewPreview>;

export const Default: Story = {};

export const Connecting: Story = {
  args: {
    streamStatus: 'connecting',
  },
};

export const Empty: Story = {
  args: {
    showEmpty: true,
  },
};
