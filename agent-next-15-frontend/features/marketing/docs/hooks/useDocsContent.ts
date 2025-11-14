'use client';

import { DOCS_HERO, DOC_NAV_ITEMS, DOC_SECTIONS, DOC_RESOURCES, DOC_GUIDES, DOC_METRICS, DOCS_FAQ } from '../constants';
import type { DocsContentState } from '../types';

export function useDocsContent(): DocsContentState {
  return {
    heroEyebrow: DOCS_HERO.eyebrow,
    heroTitle: DOCS_HERO.title,
    heroDescription: DOCS_HERO.description,
    heroUpdatedAt: DOCS_HERO.lastUpdated,
    navItems: DOC_NAV_ITEMS,
    sections: DOC_SECTIONS,
    resources: DOC_RESOURCES,
    guides: DOC_GUIDES,
    metrics: DOC_METRICS,
    faq: DOCS_FAQ,
  };
}
