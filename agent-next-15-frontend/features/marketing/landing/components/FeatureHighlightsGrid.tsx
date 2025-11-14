import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import type { FeatureHighlight } from '../types';

interface FeatureHighlightsGridProps {
  highlights: FeatureHighlight[];
}

export function FeatureHighlightsGrid({ highlights }: FeatureHighlightsGridProps) {
  return (
    <section className="space-y-6">
      <SectionHeader
        eyebrow="Product"
        title="Designed for enterprise-ready launches"
        description="Every feature ships inside a dedicated directory so you can extend the surfaces without untangling monoliths."
      />
      <div className="grid gap-4 md:grid-cols-2">
        {highlights.map((highlight) => (
          <GlassPanel key={highlight.title} className="space-y-4">
            <div className="flex items-center gap-3">
              <highlight.icon className="h-5 w-5 text-foreground/70" />
              <div>
                <p className="text-lg font-semibold text-foreground">{highlight.title}</p>
                <p className="text-sm text-foreground/70">{highlight.description}</p>
              </div>
            </div>
            <ul className="space-y-2 text-sm text-foreground/70">
              {highlight.bullets.map((bullet) => (
                <li key={bullet}>• {bullet}</li>
              ))}
            </ul>
          </GlassPanel>
        ))}
      </div>
    </section>
  );
}
