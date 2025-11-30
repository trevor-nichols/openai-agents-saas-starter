import type { MetadataRoute } from 'next';

import { getLastModified } from '@/lib/seo/deployInfo';
import { getPriorityForPath, getPublicPaths } from '@/lib/seo/publicPaths';
import { buildAbsoluteUrl } from '@/lib/seo/siteUrl';

export const dynamic = 'force-static';

export default function sitemap(): MetadataRoute.Sitemap {
  const lastModified = getLastModified();

  return getPublicPaths().map((path) => ({
    url: buildAbsoluteUrl(path),
    lastModified,
    changeFrequency: 'weekly',
    priority: getPriorityForPath(path),
  }));
}
