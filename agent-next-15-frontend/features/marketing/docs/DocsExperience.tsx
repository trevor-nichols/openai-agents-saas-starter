'use client';

import { CtaBand, FaqSection } from '@/features/marketing/components';
import { useMarketingAnalytics } from '@/features/marketing/hooks/useMarketingAnalytics';

import { DOCS_CTA } from './constants';
import { DocsHero, DocSectionsGrid, ResourceLinks, GuideGrid, MetricsStrip } from './components';
import { useDocsContent } from './hooks';

export function DocsExperience() {
  const content = useDocsContent();
  const { trackCtaClick } = useMarketingAnalytics();

  return (
    <div className="mx-auto flex w-full max-w-6xl flex-col gap-12 px-6 py-16">
      <DocsHero
        eyebrow={content.heroEyebrow}
        title={content.heroTitle}
        description={content.heroDescription}
        updatedAt={content.heroUpdatedAt}
        navItems={content.navItems}
        primaryCta={DOCS_CTA.primaryCta}
        secondaryCta={DOCS_CTA.secondaryCta}
        onCtaClick={trackCtaClick}
      />

      <MetricsStrip metrics={content.metrics} />

      <DocSectionsGrid
        sections={content.sections}
        onCtaClick={({ location, cta }) => trackCtaClick({ location, cta })}
      />

      <ResourceLinks
        resources={content.resources}
        onResourceClick={({ location, cta }) => trackCtaClick({ location, cta })}
      />

      <GuideGrid
        guides={content.guides}
        onGuideClick={({ location, cta }) => trackCtaClick({ location, cta })}
      />

      <FaqSection items={content.faq} title="Docs & tooling" eyebrow="FAQ" />

      <CtaBand config={DOCS_CTA} onCtaClick={trackCtaClick} />
    </div>
  );
}
