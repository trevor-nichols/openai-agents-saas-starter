import { GlassPanel, InlineTag, KeyValueList } from '@/components/ui/foundation';
import { EmptyState, ErrorState, SkeletonPanel } from '@/components/ui/states';
import type { TenantSubscription } from '@/lib/types/billing';

interface CurrentSubscriptionCardProps {
  subscription?: TenantSubscription | null;
  isLoading: boolean;
  error?: Error | null;
  onRetry: () => void;
}

export function CurrentSubscriptionCard({ subscription, isLoading, error, onRetry }: CurrentSubscriptionCardProps) {
  if (error) {
    return (
      <GlassPanel>
        <ErrorState title="Subscription unavailable" message="We could not load your current plan. Try refreshing the page." onRetry={onRetry} />
      </GlassPanel>
    );
  }

  if (isLoading) {
    return (
      <GlassPanel>
        <SkeletonPanel lines={3} />
      </GlassPanel>
    );
  }

  if (!subscription) {
    return (
      <GlassPanel>
        <EmptyState title="No subscription detected" description="Start a subscription from the plan catalog below." />
      </GlassPanel>
    );
  }

  return (
    <GlassPanel className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-foreground/60">Current subscription</p>
          <h2 className="text-2xl font-semibold text-foreground">{subscription.plan_code ?? 'No plan found'}</h2>
          <p className="text-sm text-foreground/60">Status · {subscription.status ?? 'unknown'}</p>
        </div>
        <InlineTag tone={subscription.auto_renew ? 'positive' : 'warning'}>
          Auto renew {subscription.auto_renew ? 'on' : 'off'}
        </InlineTag>
      </div>
      <KeyValueList
        columns={2}
        items={[
          { label: 'Plan', value: subscription.plan_code },
          { label: 'Seats', value: subscription.seat_count ?? '—' },
          { label: 'Billing contact', value: subscription.billing_email ?? 'Not set' },
          {
            label: 'Next billing',
            value: subscription.current_period_end
              ? new Date(subscription.current_period_end).toLocaleDateString()
              : 'TBD',
          },
        ]}
      />
    </GlassPanel>
  );
}
