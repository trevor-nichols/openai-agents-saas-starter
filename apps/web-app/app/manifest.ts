import type { MetadataRoute } from 'next';

import { getSiteUrl } from '@/lib/seo/siteUrl';

const THEME_COLOR = '#0f172a';
const BACKGROUND_COLOR = '#0b1220';

export default function manifest(): MetadataRoute.Manifest {
  const siteUrl = getSiteUrl();

  return {
    name: 'OpenAI Agents SaaS Starter',
    short_name: 'Agents Starter',
    description: 'Launch an AI agent SaaS fast with the OpenAI Agents SDK, FastAPI backend, and Next.js 16 frontend.',
    start_url: '/',
    scope: '/',
    display: 'standalone',
    theme_color: THEME_COLOR,
    background_color: BACKGROUND_COLOR,
    lang: 'en',
    dir: 'ltr',
    orientation: 'portrait',
    categories: ['productivity', 'business', 'developer-tools'],
    prefer_related_applications: false,
    icons: [
      {
        src: `${siteUrl}/icons/icon-192.png`,
        sizes: '192x192',
        type: 'image/png',
        purpose: 'any',
      },
      {
        src: `${siteUrl}/icons/icon-512.png`,
        sizes: '512x512',
        type: 'image/png',
        purpose: 'maskable',
      },
    ],
  };
}
