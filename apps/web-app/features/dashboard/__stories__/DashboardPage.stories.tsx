'use client';

import type { Meta, StoryObj } from '@storybook/react';

import { SectionHeader } from '@/components/ui/foundation';
import { Button } from '@/components/ui/button';

import { ActivityFeed } from '../components/ActivityFeed';
import { BillingPreview } from '../components/BillingPreview';
import { KpiGrid } from '../components/KpiGrid';
import { QuickActions } from '../components/QuickActions';
import { DASHBOARD_COPY } from '../constants';
import type { ActivityFeedItem, DashboardKpi } from '../types';
import { activityItems, billingPreviewSummary, dashboardKpis, quickActions } from './fixtures';

type DashboardPreviewProps = {
  kpis?: DashboardKpi[];
  kpiError?: string | null;
  isLoadingKpis?: boolean;
  activity?: ActivityFeedItem[];
  activityError?: string | null;
  isLoadingActivity?: boolean;
};

function DashboardPreview({
  kpis = dashboardKpis,
  kpiError = null,
  isLoadingKpis = false,
  activity = activityItems,
  activityError = null,
  isLoadingActivity = false,
}: DashboardPreviewProps) {
  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={DASHBOARD_COPY.header.eyebrow}
        title={DASHBOARD_COPY.header.title}
        description={DASHBOARD_COPY.header.description}
        actions={
          <Button asChild>
            <a href="/chat">{DASHBOARD_COPY.header.ctaLabel}</a>
          </Button>
        }
      />

      <KpiGrid kpis={kpis} isLoading={isLoadingKpis} error={kpiError} />

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ActivityFeed
            items={activity}
            isLoading={isLoadingActivity}
            error={activityError}
            onRefresh={() => console.log('refresh activity')}
          />
        </div>
        <div className="lg:col-span-1">
          <BillingPreview preview={billingPreviewSummary} />
        </div>
      </div>

      <QuickActions actions={quickActions} />
    </section>
  );
}

const meta: Meta<typeof DashboardPreview> = {
  title: 'Dashboard/Page',
  component: DashboardPreview,
};

export default meta;

type Story = StoryObj<typeof DashboardPreview>;

export const Default: Story = {};

export const Loading: Story = {
  args: {
    isLoadingKpis: true,
    isLoadingActivity: true,
  },
};

export const ErrorStates: Story = {
  args: {
    kpiError: 'Failed to load KPIs',
    activityError: 'Activity feed unavailable',
    activity: [],
  },
};
