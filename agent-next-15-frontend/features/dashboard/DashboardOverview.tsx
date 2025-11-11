'use client';

import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { SectionHeader } from '@/components/ui/foundation';

import { BillingPreview } from './components/BillingPreview';
import { KpiGrid } from './components/KpiGrid';
import { QuickActions } from './components/QuickActions';
import { RecentConversations } from './components/RecentConversations';
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
        eyebrow="Overview"
        title="Command center"
        description="Monitor agents, conversations, and billing health from a single glass surface."
        actions={
          <Button asChild>
            <Link href="/chat">New chat</Link>
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
