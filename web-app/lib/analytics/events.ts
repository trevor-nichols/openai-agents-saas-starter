import { createLogger } from '@/lib/logging';

export interface AnalyticsEventPayload {
  event: string;
  channel?: string;
  location?: string;
  metadata?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

const log = createLogger('analytics');

function dispatchBrowserEvent(name: string, detail: Record<string, unknown>) {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent(name, { detail }));

  const analytics = (window as typeof window & {
    analytics?: { track?: (event: string, payload: Record<string, unknown>) => void };
  }).analytics;

  if (analytics?.track) {
    try {
      analytics.track(detail.event as string, detail);
    } catch (error) {
      log.debug('Browser analytics track failed', { error });
    }
  }
}

export function trackEvent(payload: AnalyticsEventPayload): void {
  const detail = {
    ...payload,
    timestamp: new Date().toISOString(),
  } satisfies Record<string, unknown>;

  log.debug('Analytics event', detail);

  dispatchBrowserEvent('analytics:track', detail);
}
