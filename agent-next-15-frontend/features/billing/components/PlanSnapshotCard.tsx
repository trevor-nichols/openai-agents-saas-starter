import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, KeyValueList, StatCard } from '@/components/ui/foundation';
import { BILLING_COPY } from '@/features/billing/constants';
import type { PlanSnapshot } from '@/features/billing/types';
import type { BillingStreamStatus } from '@/types/billing';

import { formatStatusLabel } from '../utils/formatters';

interface PlanSnapshotCardProps {
  snapshot: PlanSnapshot;
  streamStatus: BillingStreamStatus;
}

export function PlanSnapshotCard({ snapshot, streamStatus }: PlanSnapshotCardProps) {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Current plan</p>
          <p className="text-2xl font-semibold text-foreground">{snapshot.planCode}</p>
          <p className="text-sm text-foreground/60">Subscription telemetry streams directly from Stripe.</p>
        </div>
        <InlineTag tone={snapshot.statusTone}>{snapshot.statusLabel}</InlineTag>
      </div>
      <KeyValueList
        columns={2}
        items={[
          { label: 'Seats', value: snapshot.seatCount },
          { label: 'Auto renew', value: snapshot.autoRenewLabel },
          { label: 'Current period', value: snapshot.currentPeriodLabel },
          { label: 'Trial ends', value: snapshot.trialEndsLabel },
        ]}
      />
      <div className="flex flex-wrap items-center gap-3">
        <StatCard label="Active seats" value={snapshot.seatCount} helperText="Rounded to the nearest seat" trend={{ value: 'Realtime', tone: 'neutral' }} />
        <StatCard
          label="Plan health"
          value={snapshot.statusLabel}
          trend={{ value: formatStatusLabel(streamStatus), tone: streamStatus === 'error' ? 'negative' : 'positive' }}
        />
      </div>
      <div className="flex justify-end">
        <Button asChild size="sm">
          <Link href="/billing/plans">{BILLING_COPY.overview.subscribeLabel}</Link>
        </Button>
      </div>
    </GlassPanel>
  );
}
