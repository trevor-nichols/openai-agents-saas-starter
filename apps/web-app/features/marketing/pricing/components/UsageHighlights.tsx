import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import type { UsageHighlight } from '../types';

interface UsageHighlightsProps {
  highlights: UsageHighlight[];
}

export function UsageHighlights({ highlights }: UsageHighlightsProps) {
  if (!highlights.length) {
    return null;
  }

  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Operations"
        title="Predictable billing + rollout controls"
        description="Trials, seats, and price ranges are transparent so finance teams can plan ahead."
      />
      <div className="grid gap-4 md:grid-cols-3">
        {highlights.map((highlight) => (
          <GlassPanel key={highlight.label} className="space-y-2">
            <p className="text-xs uppercase tracking-[0.3em] text-foreground/50">{highlight.label}</p>
            <p className="text-3xl font-semibold text-foreground">{highlight.value}</p>
            {highlight.helperText ? (
              <p className="text-sm text-foreground/70">{highlight.helperText}</p>
            ) : null}
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
