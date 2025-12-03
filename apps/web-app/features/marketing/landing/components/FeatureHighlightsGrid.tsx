import type { FeatureHighlight } from '../types';

interface FeatureHighlightsGridProps {
  highlights: FeatureHighlight[];
}

export function FeatureHighlightsGrid({ highlights }: FeatureHighlightsGridProps) {
  return (
    <div className="grid gap-4 md:grid-cols-2">
      {highlights.map((highlight) => (
        <div key={highlight.title} className="flex flex-col gap-4 rounded-3xl border bg-card p-6 shadow-sm transition-all hover:shadow-md">
          <div className="flex items-start gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
              <highlight.icon className="h-5 w-5" />
            </div>
            <div className="space-y-1">
              <p className="text-base font-bold text-foreground">{highlight.title}</p>
              <p className="text-sm text-muted-foreground leading-relaxed">{highlight.description}</p>
            </div>
          </div>
          <ul className="mt-2 space-y-2">
            {highlight.bullets.map((bullet) => (
              <li key={bullet} className="flex items-start gap-2 text-xs font-medium text-foreground/80">
                <div className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
                <span>{bullet}</span>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}
