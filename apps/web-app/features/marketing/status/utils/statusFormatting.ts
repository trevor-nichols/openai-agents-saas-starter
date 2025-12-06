export const DEFAULT_STATUS_DESCRIPTION = 'FastAPI, Next.js, and the async workers are all reporting healthy.';

export type BannerTone = 'positive' | 'warning' | 'default';
export type TrendTone = 'positive' | 'negative' | 'neutral';

export interface SubscriptionBanner {
  tone: BannerTone;
  title: string;
  description: string;
}

export function resolveTone(state?: string): BannerTone {
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

export function resolveTrendTone(tone: string): TrendTone {
  if (tone === 'positive') {
    return 'positive';
  }
  if (tone === 'negative') {
    return 'negative';
  }
  return 'neutral';
}

export function statusLabel(state: string): string {
  if (!state) {
    return 'Unknown';
  }
  return state.charAt(0).toUpperCase() + state.slice(1);
}

export function incidentTone(state: string): Exclude<BannerTone, 'default'> {
  return state.toLowerCase() === 'resolved' ? 'positive' : 'warning';
}

export function formatTimestamp(value: string | null | undefined): string {
  if (!value) {
    return 'Pending update';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' });
}

export function formatDateOnly(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString(undefined, { dateStyle: 'long' });
}
