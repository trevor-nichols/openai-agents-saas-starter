import { GlassPanel, InlineTag } from '@/components/ui/foundation';
import type { BillingPlan } from '@/types/billing';

import { formatCurrency, formatInterval } from '../utils/formatters';

interface PlanCardProps {
  plan: BillingPlan;
  current: boolean;
  disabled: boolean;
  onSelect: () => void;
}

export function PlanCard({ plan, current, disabled, onSelect }: PlanCardProps) {
  return (
    <button
      type="button"
      onClick={onSelect}
      className="w-full text-left focus:outline-none disabled:cursor-not-allowed"
      disabled={disabled}
      aria-disabled={disabled}
    >
      <GlassPanel className={`flex h-full flex-col justify-between gap-5 ${disabled ? 'opacity-60' : ''}`}>
        <div className="space-y-3">
          <div className="flex items-center justify-between gap-2">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{plan.code}</p>
              <h3 className="text-lg font-semibold text-foreground">{plan.name}</h3>
            </div>
            <InlineTag tone={!plan.is_active ? 'warning' : current ? 'positive' : 'default'}>
              {current ? 'Current' : plan.is_active ? 'Active' : 'Retired'}
            </InlineTag>
          </div>
          <div className="flex items-baseline gap-2">
            <p className="text-3xl font-semibold text-foreground">{formatCurrency(plan.price_cents, plan.currency)}</p>
            <span className="text-sm text-foreground/60">/ {formatInterval(plan)}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {plan.trial_days ? <InlineTag tone="default">Trial {plan.trial_days}d</InlineTag> : null}
            {plan.seat_included ? <InlineTag tone="default">{plan.seat_included} seats</InlineTag> : null}
          </div>
          {plan.features?.length ? (
            <div className="space-y-1 text-sm text-foreground/70">
              {plan.features.slice(0, 3).map((feature) => (
                <p key={feature.key} className="text-foreground/80">
                  <span className="font-semibold">{feature.display_name}:</span>{' '}
                  {feature.description ?? (feature.is_metered ? 'Metered limit' : 'Included')}
                </p>
              ))}
            </div>
          ) : null}
        </div>
      </GlassPanel>
    </button>
  );
}
