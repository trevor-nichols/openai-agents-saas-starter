export interface AnalyticsEventPayload {
  event: string;
  channel?: string;
  location?: string;
  metadata?: Record<string, unknown>;
  context?: Record<string, unknown>;
}

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
      if (process.env.NODE_ENV !== 'production') {
        console.debug('[analytics] track failed', error);
      }
    }
  }
}

export function trackEvent(payload: AnalyticsEventPayload): void {
  const detail = {
    ...payload,
    timestamp: new Date().toISOString(),
  } satisfies Record<string, unknown>;

  if (process.env.NODE_ENV !== 'production') {
    console.debug('[analytics]', detail);
  }

  dispatchBrowserEvent('analytics:track', detail);
}
