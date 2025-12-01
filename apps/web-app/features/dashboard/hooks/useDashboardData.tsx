'use client';

import { useMemo } from 'react';
import { Sparkles, TrendingUp, Wallet } from 'lucide-react';

import { useAgents } from '@/lib/queries/agents';
import { useBillingStream } from '@/lib/queries/billing';
import { useConversations } from '@/lib/queries/conversations';

import { QUICK_ACTIONS } from '../constants';
import type { BillingPreviewSummary, DashboardData, DashboardKpi, RecentConversationSummary } from '../types';

const numberFormatter = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 });

export function useDashboardData(): DashboardData {
  const { agents, isLoadingAgents, agentsError } = useAgents();
  const {
    conversationList,
    isLoadingConversations,
    error: conversationsError,
    loadConversations,
  } = useConversations();
  const { events: billingEvents, status: billingStreamStatus } = useBillingStream();

  const activeAgents = useMemo(() => agents.filter((agent) => agent.status === 'active').length, [agents]);
  const idleAgents = useMemo(() => Math.max(agents.length - activeAgents, 0), [agents, activeAgents]);

  const conversationsLast24h = conversationList.length;

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
        id: 'conversation-volume',
        label: 'Conversations (24h)',
        value: numberFormatter.format(conversationsLast24h),
        helperText: `${conversationList.length} total conversations`,
        icon: <TrendingUp className="h-4 w-4" />,
        trend: {
          value: conversationsLast24h > 0 ? '+ active' : 'Awaiting traffic',
          tone: conversationsLast24h > 0 ? 'positive' : 'neutral',
          label: 'Monitoring audit log',
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
  }, [activeAgents, agents.length, billingEvents, billingStreamStatus, conversationList.length, conversationsLast24h, idleAgents]);

  const recentConversations = useMemo<RecentConversationSummary[]>(
    () =>
      conversationList
        .slice(0, 5)
        .map((conversation) => ({
          id: conversation.id,
          title: conversation.topic_hint ?? conversation.title ?? 'Untitled conversation',
          updatedAt: conversation.updated_at,
          summary: conversation.last_message_preview ?? 'Awaiting summary',
        })),
    [conversationList]
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

  const kpiError = agentsError?.message ?? conversationsError ?? null;

  return {
    kpis,
    isLoadingKpis: isLoadingAgents || isLoadingConversations,
    kpiError,
    recentConversations,
    isLoadingConversations,
    conversationsError,
    billingPreview,
    quickActions: QUICK_ACTIONS,
    refreshConversations: loadConversations,
  } satisfies DashboardData;
}
