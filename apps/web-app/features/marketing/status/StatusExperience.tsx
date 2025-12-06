'use client';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader } from '@/components/ui/foundation';
import { StatusAlertsCard } from '@/features/marketing/components';
import { useMarketingAnalytics } from '@/features/marketing/hooks/useMarketingAnalytics';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import { apiV1Path } from '@/lib/apiPaths';
import {
  IncidentTable,
  MetricsPanel,
  OverviewPanel,
  ServiceList,
  SubscribePanel,
  VerificationBanner,
} from './components';
import { useStatusSubscriptionActions } from './hooks/useStatusSubscriptionActions';
import { formatTimestamp, resolveTone } from './utils/statusFormatting';

export function StatusExperience() {
  const { status, isLoading, error, refetch } = usePlatformStatusQuery();
  const { trackLeadSubmit, trackCtaClick } = useMarketingAnalytics();
  const { banner } = useStatusSubscriptionActions();

  const overview = status?.overview;
  const services = status?.services ?? [];
  const incidents = status?.incidents ?? [];
  const uptimeMetrics = status?.uptimeMetrics ?? [];

  const updatedLabel = status ? formatTimestamp(status.generatedAt) : 'Refreshing status…';
  const showServiceSkeletons = isLoading && services.length === 0;
  const showMetricSkeletons = isLoading && uptimeMetrics.length === 0;
  const showIncidentSkeletons = isLoading && incidents.length === 0;
  const rssHref = apiV1Path('/status/rss');

  return (
    <div className="space-y-10">
      <VerificationBanner banner={banner} />

      <SectionHeader
        eyebrow="Status"
        title="Operational visibility"
        description="Bookmark this page to monitor the FastAPI backend, Next.js frontend, and billing stream in one place."
        actions={
          <div className="flex flex-wrap items-center gap-3">
            <InlineTag tone={resolveTone(overview?.state)}>{overview?.state ?? 'Refreshing status…'}</InlineTag>
            <Badge variant="outline">Last updated {updatedLabel}</Badge>
          </div>
        }
      />

      {error ? (
        <GlassPanel className="space-y-3 border border-destructive/40">
          <p className="text-sm text-destructive">{error.message}</p>
          <Button size="sm" variant="outline" onClick={refetch}>
            Retry
          </Button>
        </GlassPanel>
      ) : null}

      <OverviewPanel description={overview?.description} />

      <StatusAlertsCard onLeadSubmit={(payload) => trackLeadSubmit(payload)} source="status-page" />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <ServiceList services={services} showSkeletons={showServiceSkeletons} />

        <div className="space-y-4">
          <MetricsPanel metrics={uptimeMetrics} showSkeletons={showMetricSkeletons} />
          <SubscribePanel rssHref={rssHref} onCtaClick={trackCtaClick} />
        </div>
      </div>

      <IncidentTable incidents={incidents} showSkeletons={showIncidentSkeletons} />
    </div>
  );
}
