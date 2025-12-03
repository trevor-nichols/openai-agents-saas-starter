'use client';

import { useMemo } from 'react';
import { Sparkles, TrendingUp, Wallet } from 'lucide-react';

import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useActivityFeed } from '@/lib/queries/activity';
import { useActivityStream } from '@/lib/queries/useActivityStream';
import { mergeActivityEvents, toActivityDisplayItem } from '@/lib/utils/activity';

import { QUICK_ACTIONS } from '../constants';
import type { ActivityFeedItem, BillingPreviewSummary, DashboardData, DashboardKpi } from '../types';

const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

export function useDashboardData(): DashboardData {
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const {
    activity,
    isLoading: isLoadingActivity,
    error: activityError,
    refresh: refreshActivity,
  } = useActivityFeed({ limit: 20 });
  const { events: liveActivity } = useActivityStream({ enabled: true });
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const idleAgents = useMemo(() => Math.max(agents.length - activeAgents, 0), [agents, activeAgents]);

  const recentActivityCount = activity.length;

  const kpis = useMemo<DashboardKpi[]>(() => {
    const utilization = agents.length ? Math.round((activeAgents / agents.length) * 100) : 0;
    return [
      {
        id: 'agents-online',
        label: 'Agents online',
        value: numberFormatter.format(activeAgents),
        helperText: `${idleAgents} off duty`,
        icon: <Sparkles className="h-4 w-4" />,
        trend: {
          value: `${utilization}% util`,
          tone: utilization > 65 ? 'positive' : 'neutral',
          label: `${agents.length} registered`,
        },
      },
      {
        id: 'activity-volume',
        label: 'Recent activity',
        value: numberFormatter.format(recentActivityCount),
        helperText: `${activity.length} events cached`,
        icon: <TrendingUp className="h-4 w-4" />,
        trend: {
          value: recentActivityCount > 0 ? 'Live' : 'Awaiting traffic',
          tone: recentActivityCount > 0 ? 'positive' : 'neutral',
          label: activity[0]?.action ?? 'Monitoring audit log',
        },
      },
      {
        id: 'billing-events',
        label: 'Billing events',
        value: numberFormatter.format(billingEvents.length),
        helperText: 'Last 20 events retained',
        icon: <Wallet className="h-4 w-4" />,
        trend: {
          value: billingStreamStatus === 'open' ? 'Live stream' : billingStreamStatus,
          tone: billingStreamStatus === 'error' ? 'negative' : 'neutral',
          label: billingEvents[0]?.summary ?? 'Awaiting first event',
        },
      },
    ];
  }, [
    activeAgents,
    activity,
    agents.length,
    billingEvents,
    billingStreamStatus,
    idleAgents,
    recentActivityCount,
  ]);

  const mergedActivity = useMemo(
    () => mergeActivityEvents(liveActivity, activity, 20),
    [activity, liveActivity],
  );

  const activityFeed = useMemo<ActivityFeedItem[]>(
    () => mergedActivity.slice(0, 8).map(toActivityDisplayItem),
    [mergedActivity],
  );

  const billingPreview = useMemo<BillingPreviewSummary>(() => {
    const subscriptionEvent = billingEvents.find((event) => event.subscription);
    const invoiceEvent = billingEvents.find((event) => event.invoice);
    const nextInvoiceLabel = invoiceEvent?.invoice
      ? new Intl.NumberFormat('en-US', { style: 'currency', currency: invoiceEvent.invoice.currency ?? 'USD' }).format(
          (invoiceEvent.invoice.amount_due_cents ?? 0) / 100
        )
      : undefined;

    return {
      planCode: subscriptionEvent?.subscription?.plan_code ?? 'Pending plan',
      planStatus: subscriptionEvent?.subscription?.status ?? 'unknown',
      streamStatus: billingStreamStatus,
      nextInvoiceLabel,
      latestEvents: billingEvents.slice(0, 4),
    } satisfies BillingPreviewSummary;
  }, [billingEvents, billingStreamStatus]);

  const kpiError = agentsError?.message ?? activityError ?? null;

  return {
    kpis,
    isLoadingKpis: isLoadingAgents || isLoadingActivity,
    kpiError,
    activityFeed,
    isLoadingActivity,
    activityError,
    billingPreview,
    quickActions: QUICK_ACTIONS,
    refreshActivity,
  } satisfies DashboardData;
}
