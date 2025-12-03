import { ArrowRight } from 'lucide-react';

import { GlassPanel, SectionHeader } from '@/components/ui/foundation';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface PlanShowcaseProps {
  plans: Array<{ name: string; price: string; cadence: string; summary: string }>;
}

export function PlanShowcase({ plans }: PlanShowcaseProps) {
  if (!plans.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Pricing"
        title="Plans that scale with your roadmap"
        description="Start with the starter tier for proofs of concept, then grow into enterprise without rewriting billing surfaces."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {plans.map((plan, index) => (
          <GlassPanel key={plan.name} className="space-y-4 border border-white/10">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">Tier {index + 1}</p>
                <p className="text-lg font-semibold text-foreground">{plan.name}</p>
              </div>
              {index === plans.length - 1 ? <Badge variant="outline">Most popular</Badge> : null}
            </div>
            <div className="flex items-baseline gap-2">
              <p className="text-3xl font-semibold text-foreground">{plan.price}</p>
              <span className="text-sm text-foreground/60">/ {plan.cadence}</span>
            </div>
            <p className="text-sm text-foreground/70">{plan.summary}</p>
          </GlassPanel>
        ))}

        <GlassPanel className="col-span-full flex flex-col items-start justify-between gap-4 border border-primary/20 bg-primary/5 p-6 sm:flex-row sm:items-center">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <p className="text-lg font-semibold text-foreground">Enterprise</p>
              <Badge variant="secondary" className="bg-primary/20 text-primary hover:bg-primary/30">
                Custom
              </Badge>
            </div>
            <p className="text-sm text-foreground/70">
              Volume discounts, SLA guarantees, and dedicated support channels.
            </p>
          </div>
          <Button variant="outline" className="shrink-0 gap-2 border-primary/20 hover:bg-primary/10">
            Contact sales <ArrowRight className="h-4 w-4" />
          </Button>
        </GlassPanel>
      </div>
    </section>
  );
}
