'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';

import { BillingPreview } from './components/BillingPreview';
import { KpiGrid } from './components/KpiGrid';
import { QuickActions } from './components/QuickActions';
import { RecentConversations } from './components/RecentConversations';
import { DASHBOARD_COPY } from './constants';
import { useDashboardData } from './hooks/useDashboardData';

export function DashboardOverview() {
  const {
    kpis,
    isLoadingKpis,
    kpiError,
    recentConversations,
    isLoadingConversations,
    conversationsError,
    billingPreview,
    quickActions,
    refreshConversations,
  } = useDashboardData();

  return (
    <section className="space-y-10">
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

      <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
        <RecentConversations
          conversations={recentConversations}
          isLoading={isLoadingConversations}
          error={conversationsError}
          onRefresh={refreshConversations}
        />
        <BillingPreview preview={billingPreview} />
      </div>

      <QuickActions actions={quickActions} />
    </section>
  );
}
