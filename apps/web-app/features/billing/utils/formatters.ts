import type { BillingPlan } from '@/types/billing';
import type { StatusTone } from '../types';

export function formatCurrency(amountCents?: number | null, currency: string = 'USD'): string {
  if (amountCents == null) {
    return '—';
  }
  return new Intl.NumberFormat('en-US', { style: 'currency', currency }).format(amountCents / 100);
}

export function formatDate(value?: string | null): string {
  if (!value) {
    return '—';
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return '—';
  }
  return date.toLocaleDateString();
}

export function formatPeriod(start?: string | null, end?: string | null): string {
  if (!start && !end) {
    return '—';
  }
  if (!start || !end) {
    return formatDate(start ?? end ?? undefined);
  }
  return `${formatDate(start)} → ${formatDate(end)}`;
}

export function resolveStatusTone(value?: string | null): StatusTone {
  if (!value) {
    return 'default';
  }
  const normalized = value.toLowerCase();
  if (['active', 'open', 'trialing', 'live'].includes(normalized)) {
    return 'positive';
  }
  if (['error', 'past_due', 'canceled', 'disconnected', 'degraded'].includes(normalized)) {
    return 'warning';
  }
  return 'default';
}

export function formatStatusLabel(value?: string | null): string {
  if (!value) {
    return 'unknown';
  }
  if (value === 'open') {
    return 'live';
  }
  return value;
}

export function formatInterval(plan: BillingPlan): string {
  return plan.interval_count > 1 ? `${plan.interval_count} ${plan.interval}s` : plan.interval;
}

export function formatCardBrand(brand?: string | null): string {
  if (!brand) {
    return 'Card';
  }
  const normalized = brand.toLowerCase();
  if (normalized === 'amex') {
    return 'Amex';
  }
  if (normalized === 'mastercard') {
    return 'Mastercard';
  }
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

export function formatCardExpiry(expMonth?: number | null, expYear?: number | null): string {
  if (!expMonth || !expYear) {
    return '—';
  }
  const month = String(expMonth).padStart(2, '0');
  const year = String(expYear).slice(-2);
  return `${month}/${year}`;
}
