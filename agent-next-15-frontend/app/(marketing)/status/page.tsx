'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { GlassPanel, InlineTag, SectionHeader, StatCard } from '@/components/ui/foundation';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { usePlatformStatusQuery } from '@/lib/queries/status';
import { unsubscribeStatusSubscription, verifyStatusSubscriptionToken } from '@/lib/api/statusSubscriptions';

const DEFAULT_STATUS_DESCRIPTION = 'FastAPI, Next.js, and the async workers are all reporting healthy.';

export default function StatusPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const verificationToken = searchParams.get('token');
  const verificationParam = searchParams.get('verification');
  const unsubscribeToken = searchParams.get('unsubscribe_token');
  const unsubscribeParam = searchParams.get('unsubscribe');
  const subscriptionIdentifier = searchParams.get('subscription_id');
  const verificationAttemptedRef = useRef(false);
  const unsubscribeAttemptedRef = useRef(false);
  const [verificationInProgress, setVerificationInProgress] = useState(false);
  const [unsubscribeInProgress, setUnsubscribeInProgress] = useState(false);
  const { status, isLoading, error, refetch } = usePlatformStatusQuery();

  const overview = status?.overview;
  const services = status?.services ?? [];
  const incidents = status?.incidents ?? [];
  const uptimeMetrics = status?.uptimeMetrics ?? [];

  const updatedLabel = status ? formatTimestamp(status.generatedAt) : 'Refreshing status…';
  const showServiceSkeletons = isLoading && services.length === 0;
  const showMetricSkeletons = isLoading && uptimeMetrics.length === 0;
  const showIncidentSkeletons = isLoading && incidents.length === 0;

  useEffect(() => {
    if (!verificationToken || verificationAttemptedRef.current) {
      return;
    }

    verificationAttemptedRef.current = true;
    setVerificationInProgress(true);

    const redirectWithStatus = (state: 'success' | 'error') => {
      const params = new URLSearchParams(window.location.search);
      params.delete('token');
      params.delete('subscription_id');
      params.set('verification', state);
      const search = params.toString();
      router.replace(search ? `/status?${search}` : '/status', { scroll: false });
    };

    verifyStatusSubscriptionToken(verificationToken)
      .then(() => {
        redirectWithStatus('success');
      })
      .catch(() => {
        redirectWithStatus('error');
      })
      .finally(() => {
        setVerificationInProgress(false);
      });
  }, [verificationToken, router]);

  useEffect(() => {
    if (!unsubscribeToken || unsubscribeAttemptedRef.current) {
      return;
    }
    const redirectWithStatus = (state: 'success' | 'error') => {
      const params = new URLSearchParams(window.location.search);
      params.delete('unsubscribe_token');
      if (state === 'success' || !subscriptionIdentifier) {
        params.delete('subscription_id');
      }
      params.set('unsubscribe', state);
      const search = params.toString();
      router.replace(search ? `/status?${search}` : '/status', { scroll: false });
    };

    if (!subscriptionIdentifier) {
      unsubscribeAttemptedRef.current = true;
      redirectWithStatus('error');
      return;
    }

    unsubscribeAttemptedRef.current = true;
    setUnsubscribeInProgress(true);

    unsubscribeStatusSubscription(unsubscribeToken, subscriptionIdentifier)
      .then(() => {
        redirectWithStatus('success');
      })
      .catch(() => {
        redirectWithStatus('error');
      })
      .finally(() => {
        setUnsubscribeInProgress(false);
      });
  }, [unsubscribeToken, subscriptionIdentifier, router]);

  const verificationBanner = useMemo(() => {
    if (verificationInProgress) {
      return {
        tone: 'default' as const,
        title: 'Confirming subscription…',
        description: 'Hang tight while we verify your email link.',
      };
    }

    if (unsubscribeInProgress) {
      return {
        tone: 'default' as const,
        title: 'Updating preferences…',
        description: 'Processing your unsubscribe request.',
      };
    }

    if (verificationParam === 'success') {
      return {
        tone: 'positive' as const,
        title: 'Subscription confirmed',
        description: 'You will now receive email alerts whenever status changes.',
      };
    }

    if (verificationParam === 'error') {
      return {
        tone: 'warning' as const,
        title: 'Unable to confirm subscription',
        description: 'The verification link may have expired. Request a new email to try again.',
      };
    }

    if (unsubscribeParam === 'success') {
      return {
        tone: 'positive' as const,
        title: 'Subscription removed',
        description: 'You will no longer receive email updates from this list.',
      };
    }

    if (unsubscribeParam === 'error') {
      return {
        tone: 'warning' as const,
        title: 'Unable to unsubscribe',
        description: 'The unsubscribe link may have expired. Request a fresh email to try again.',
      };
    }

    return null;
  }, [verificationParam, unsubscribeParam, verificationInProgress, unsubscribeInProgress]);

  return (
    <div className="space-y-10">
      {verificationBanner ? (
        <GlassPanel className="flex flex-col gap-2 border-white/10 bg-white/10">
          <div className="flex items-center gap-3">
            <InlineTag tone={verificationBanner.tone}>{verificationBanner.title}</InlineTag>
          </div>
          <p className="text-sm text-foreground/80">{verificationBanner.description}</p>
        </GlassPanel>
      ) : null}
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

      <GlassPanel className="space-y-3">
        <p className="text-base text-foreground/80">{overview?.description ?? DEFAULT_STATUS_DESCRIPTION}</p>
        <Separator className="border-white/5" />
        <div className="flex flex-wrap gap-3 text-sm text-foreground/60">
          <span>• Backend: `/health` & `/health/ready`</span>
          <span>• Frontend: App Router diagnostics</span>
          <span>• Workers: Stripe dispatcher, retry worker</span>
        </div>
      </GlassPanel>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
        <div className="space-y-6">
          {showServiceSkeletons
            ? [1, 2, 3].map((item) => <ServiceSkeleton key={`service-skeleton-${item}`} />)
            : services.map((service) => (
                <GlassPanel key={service.name} className="space-y-4">
                  <div className="flex flex-wrap items-start justify-between gap-4">
                    <div>
                      <h3 className="text-lg font-semibold text-foreground">{service.name}</h3>
                      <p className="text-sm text-foreground/60">{service.description}</p>
                    </div>
                    <InlineTag tone={resolveTone(service.status)}>{statusLabel(service.status)}</InlineTag>
                  </div>
                  <div className="flex flex-wrap items-center justify-between text-xs text-foreground/60">
                    <span>Owner · {service.owner}</span>
                    <span>Last incident · {formatTimestamp(service.lastIncidentAt)}</span>
                  </div>
                </GlassPanel>
              ))}
        </div>

        <div className="space-y-4">
          {showMetricSkeletons
            ? [1, 2, 3].map((item) => <MetricSkeleton key={`metric-skeleton-${item}`} />)
            : uptimeMetrics.map((metric) => (
                <StatCard
                  key={metric.label}
                  label={metric.label}
                  value={metric.value}
                  helperText={metric.helperText}
                  trend={{ value: metric.trendValue, tone: resolveTrendTone(metric.trendTone) }}
                />
              ))}
          <GlassPanel className="space-y-3">
            <h4 className="text-base font-semibold text-foreground">Subscribe for alerts</h4>
            <p className="text-sm text-foreground/70">Hook this status feed into your tooling via RSS or our CLI.</p>
            <div className="flex flex-wrap gap-2">
              <Button asChild size="sm">
                <Link href="/api/status/rss">RSS Feed</Link>
              </Button>
              <Button asChild size="sm" variant="outline">
                <Link href="mailto:status@anything.agents">Email ops</Link>
              </Button>
            </div>
          </GlassPanel>
        </div>
      </div>

      <div className="space-y-4">
        <SectionHeader
          eyebrow="Incident log"
          title="Recent events"
          description="Full incident timelines live in Linear, but this snapshot keeps marketing visitors informed."
        />
        <GlassPanel>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Date</TableHead>
                <TableHead>Service</TableHead>
                <TableHead>Impact</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {showIncidentSkeletons
                ? [1, 2, 3].map((item) => <IncidentSkeleton key={`incident-skeleton-${item}`} />)
                : incidents.length > 0
                  ? incidents.map((incident) => (
                      <TableRow key={incident.id}>
                        <TableCell className="font-medium">{formatDateOnly(incident.occurredAt)}</TableCell>
                        <TableCell>{incident.service}</TableCell>
                        <TableCell className="text-foreground/70">{incident.impact}</TableCell>
                        <TableCell>
                          <InlineTag tone={incidentTone(incident.state)}>{incident.state}</InlineTag>
                        </TableCell>
                      </TableRow>
                    ))
                  : (
                      <TableRow>
                        <TableCell colSpan={4} className="text-center text-sm text-foreground/60">
                          No incidents recorded in the current window.
                        </TableCell>
                      </TableRow>
                    )}
            </TableBody>
            <TableCaption>Incident metadata syncs nightly from the real status board.</TableCaption>
          </Table>
        </GlassPanel>
      </div>
    </div>
  );
}

function resolveTone(state?: string): 'positive' | 'warning' | 'default' {
  if (!state) {
    return 'default';
  }
  const normalized = state.toLowerCase();
  if (normalized.includes('degraded') || normalized.includes('incident') || normalized.includes('maintenance')) {
    return 'warning';
  }
  if (normalized.includes('operational') || normalized.includes('resolved')) {
    return 'positive';
  }
  return 'default';
}

function resolveTrendTone(tone: string): 'positive' | 'negative' | 'neutral' {
  if (tone === 'positive') {
    return 'positive';
  }
  if (tone === 'negative') {
    return 'negative';
  }
  return 'neutral';
}

function statusLabel(state: string): string {
  if (!state) {
    return 'Unknown';
  }
  return state.charAt(0).toUpperCase() + state.slice(1);
}

function incidentTone(state: string): 'positive' | 'warning' {
  return state.toLowerCase() === 'resolved' ? 'positive' : 'warning';
}

function formatTimestamp(value: string | null | undefined): string {
  if (!value) {
    return 'Pending update';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

function formatDateOnly(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(undefined, { dateStyle: 'long' });
}

function ServiceSkeleton() {
  return (
    <GlassPanel className="space-y-4">
      <div className="flex flex-col gap-2">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-72" />
      </div>
      <div className="flex justify-between">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-4 w-32" />
      </div>
    </GlassPanel>
  );
}

function MetricSkeleton() {
  return (
    <GlassPanel className="space-y-3">
      <Skeleton className="h-4 w-32" />
      <Skeleton className="h-6 w-24" />
      <Skeleton className="h-4 w-40" />
    </GlassPanel>
  );
}

function IncidentSkeleton() {
  return (
    <TableRow>
      <TableCell>
        <Skeleton className="h-4 w-32" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-40" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-52" />
      </TableCell>
      <TableCell>
        <Skeleton className="h-4 w-20" />
      </TableCell>
    </TableRow>
  );
}
