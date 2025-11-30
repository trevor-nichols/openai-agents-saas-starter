import { GlassPanel, SectionHeader } from '@/components/ui/foundation';

import type { StaticPageContent } from './content';

interface StaticPageProps {
  content: StaticPageContent;
}

export function StaticPage({ content }: StaticPageProps) {
  return (
    <div className="mx-auto w-full max-w-4xl space-y-10 py-12">
      <SectionHeader
        eyebrow={content.eyebrow}
        title={content.title}
        description={content.description}
      />

      {content.updated ? (
        <p className="text-sm text-foreground/60">Last updated: {content.updated}</p>
      ) : null}

      <div className="space-y-6">
        {content.sections.map((section) => (
          <GlassPanel key={section.title} className="space-y-3 border border-white/10">
            <div className="space-y-2">
              <p className="text-sm font-semibold uppercase tracking-[0.25em] text-foreground/60">{section.title}</p>
              <p className="text-foreground/80">{section.body}</p>
            </div>
            {section.bullets ? (
              <ul className="list-inside list-disc space-y-1 text-sm text-foreground/70">
                {section.bullets.map((bullet) => (
                  <li key={`${section.title}-${bullet}`}>{bullet}</li>
                ))}
              </ul>
            ) : null}
            {section.aside ? <div>{section.aside}</div> : null}
          </GlassPanel>
        ))}
      </div>
    </div>
  );
}
