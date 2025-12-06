'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';

import { BillingPreview } from './components/BillingPreview';
import { KpiGrid } from './components/KpiGrid';
import { QuickActions } from './components/QuickActions';
import { ActivityFeed } from './components/ActivityFeed';
import { DASHBOARD_COPY } from './constants';
import { useDashboardData } from './hooks/useDashboardData';

export function DashboardOverview() {
  const {
    kpis,
    isLoadingKpis,
    kpiError,
    activityFeed,
    isLoadingActivity,
    activityError,
    billingPreview,
    quickActions,
    refreshActivity,
  } = useDashboardData();

  return (
    <section className="space-y-8">
      <SectionHeader
        eyebrow={DASHBOARD_COPY.header.eyebrow}
        title={DASHBOARD_COPY.header.title}
        description={DASHBOARD_COPY.header.description}
        actions={
          <Button asChild>
            <Link href="/chat">{DASHBOARD_COPY.header.ctaLabel}</Link>
          </Button>
        }
      />

      <KpiGrid kpis={kpis} isLoading={isLoadingKpis} error={kpiError} />

      <div className="grid gap-8 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <ActivityFeed
            items={activityFeed}
            isLoading={isLoadingActivity}
            error={activityError}
            onRefresh={refreshActivity}
          />
        </div>
        <div className="lg:col-span-1">
          <BillingPreview preview={billingPreview} />
        </div>
      </div>

      <QuickActions actions={quickActions} />
    </section>
  );
}
