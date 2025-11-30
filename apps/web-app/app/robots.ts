import type { MetadataRoute } from 'next';

import { buildAbsoluteUrl, getSiteUrl } from '@/lib/seo/siteUrl';
import { DISALLOWED_PATHS } from '@/lib/seo/disallowedPaths';

export const dynamic = 'force-static';

export default function robots(): MetadataRoute.Robots {
  const host = getSiteUrl();

  return {
    rules: [
      {
        userAgent: '*',
        allow: '/',
        disallow: [...DISALLOWED_PATHS],
      },
    ],
    sitemap: [buildAbsoluteUrl('/sitemap.xml')],
    host,
  };
}
