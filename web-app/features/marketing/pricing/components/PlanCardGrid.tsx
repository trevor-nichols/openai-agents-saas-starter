import Link from 'next/link';

import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag } from '@/components/ui/foundation';

import type { PlanCardSnapshot } from '../types';

interface PlanCardGridProps {
  plans: PlanCardSnapshot[];
  onPlanCtaClick: (plan: PlanCardSnapshot) => void;
  primaryCtaHref: string;
}

export function PlanCardGrid({ plans, onPlanCtaClick, primaryCtaHref }: PlanCardGridProps) {
  return (
    <section className="space-y-6">
      <div className="flex flex-col gap-2">
        <h2 className="text-3xl font-semibold text-foreground">Choose the plan that fits</h2>
        <p className="text-foreground/70">Every plan includes agents, billing, tenant settings, and observability. Upgrade anytime.</p>
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {plans.map((plan) => (
          <GlassPanel key={plan.code} className="flex flex-col justify-between gap-5 border border-white/10">
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{plan.code}</p>
                  <p className="text-lg font-semibold text-foreground">{plan.name}</p>
                </div>
                <InlineTag tone={plan.badges.includes('Retired') ? 'warning' : 'default'}>
                  {plan.badges[0] ?? 'Active'}
                </InlineTag>
              </div>
              <div className="flex items-baseline gap-2">
                <p className="text-3xl font-semibold text-foreground">{plan.priceLabel}</p>
                <span className="text-sm text-foreground/60">/ {plan.cadenceLabel}</span>
              </div>
              <p className="text-sm text-foreground/70">{plan.summary}</p>
              <ul className="space-y-2 text-sm text-foreground/70">
                {plan.highlights.map((highlight) => (
                  <li key={`${plan.code}-${highlight}`}>• {highlight}</li>
                ))}
              </ul>
            </div>
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {plan.badges.map((badge) => (
                  <InlineTag key={`${plan.code}-${badge}`} tone="default">
                    {badge}
                  </InlineTag>
                ))}
              </div>
              <Button className="w-full" asChild>
                <Link
                  href={`${primaryCtaHref}?plan=${plan.code}`}
                  onClick={() => onPlanCtaClick(plan)}
                >
                  Choose {plan.name}
                </Link>
              </Button>
            </div>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
