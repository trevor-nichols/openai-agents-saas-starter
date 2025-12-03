import { Suspense } from 'react';
import type { ReactNode } from 'react';

import { MarketingFooter } from './_components/marketing-footer';
import { MarketingHeader } from './_components/marketing-header';

import { fetchPlatformStatusSnapshot } from '@/lib/server/services/status';
import type { PlatformStatusResponse } from '@/lib/api/client/types.gen';

interface MarketingLayoutProps {
  children: ReactNode;
}

export default function MarketingLayout({ children }: MarketingLayoutProps) {
  return (
    <div className="relative flex min-h-screen flex-col overflow-hidden bg-background text-foreground">
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top,_rgba(110,181,255,0.18),_transparent_45%)]" />

      <MarketingHeader />

      <main className="flex-1">
        <div className="mx-auto w-full max-w-6xl px-6 py-16">
          {children}
        </div>
      </main>

      <Suspense fallback={<MarketingFooter status={null} />}>
        <MarketingFooterWithStatus />
      </Suspense>
    </div>
  );
}

async function MarketingFooterWithStatus() {
  const status = await fetchMarketingStatus();
  return <MarketingFooter status={status} />;
}

async function fetchMarketingStatus(): Promise<PlatformStatusResponse | null> {
  try {
    const payload = await fetchPlatformStatusSnapshot();
    return payload;
  } catch (error) {
    console.debug('[marketing-layout] Failed to load platform status', error);
    return null;
  }
}
